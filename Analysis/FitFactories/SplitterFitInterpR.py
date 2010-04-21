#!/usr/bin/python

##################
# LatGaussFitFRTC.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################

import scipy
#from scipy.signal import interpolate
#import scipy.ndimage as ndimage
from pylab import *
import copy_reg
import numpy
import types
import cPickle

from PYME.Analysis._fithelpers import *

def pickleSlice(slice):
        return unpickleSlice, (slice.start, slice.stop, slice.step)

def unpickleSlice(start, stop, step):
        return slice(start, stop, step)

copy_reg.pickle(slice, pickleSlice, unpickleSlice)



def f_Interp3d2c(p, interpolator, Xg, Yg, Zg, Xr, Yr, Zr, *args):
    """3D PSF model function with constant background - parameter vector [A, x0, y0, z0, background]"""
    Ag, Ar, x0, y0, z0, bG, bR = p

    #make sure our model is big enough to stretch to our current position
    xm = len(Xg)/2
    dx = min((interpolator.shape[0] - len(Xg))/2, xm) - 2

    ym = len(Yg)/2
    dy = min((interpolator.shape[1] - len(Yg))/2, ym) - 2
    
    x0 = min(max(x0, Xg[xm - dx]), Xg[dx + xm])
    y0 = min(max(y0, Yg[ym - dy]), Yg[dy + ym])
    z0 = min(max(z0, max(Zg[0], Zr[0]) + interpolator.IntZVals[2]), min(Zg[0], Zr[0]) + interpolator.IntZVals[-2])

    g = interpolator.interp(Xg - x0 + 1, Yg - y0 + 1, Zg[0] - z0 + 1)*Ag + bG
    r = interpolator.interp(Xr - x0 + 1, Yr - y0 + 1, Zr[0] - z0 + 1)*Ar + bR

    return numpy.concatenate((g,r), 2)


def replNoneWith1(n):
	if n == None:
		return 1
	else:
		return n



fresultdtype=[('tIndex', '<i4'),('fitResults', [('Ag', '<f4'),('Ar', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('backgroundG', '<f4'),('backgroundR', '<f4')]),('fitError', [('Ag', '<f4'),('Ar', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('backgroundG', '<f4'),('backgroundR', '<f4')]), ('resultCode', '<i4'), ('slicesUsed', [('x', [('start', '<i4'),('stop', '<i4'),('step', '<i4')]),('y', [('start', '<i4'),('stop', '<i4'),('step', '<i4')]),('z', [('start', '<i4'),('stop', '<i4'),('step', '<i4')])]),('startParams', [('Ag', '<f4'),('Ar', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('backgroundG', '<f4'), ('backgroundR', '<f4')]), ('nchi2', '<f4')]

def PSFFitResultR(fitResults, metadata, slicesUsed=None, resultCode=-1, fitErr=None, startParams=None, nchi2=-1):
	if slicesUsed == None:
		slicesUsed = ((-1,-1,-1),(-1,-1,-1),(-1,-1,-1))
	else: 		
		slicesUsed = ((slicesUsed[0].start,slicesUsed[0].stop,replNoneWith1(slicesUsed[0].step)),(slicesUsed[1].start,slicesUsed[1].stop,replNoneWith1(slicesUsed[1].step)),(slicesUsed[2].start,slicesUsed[2].stop,replNoneWith1(slicesUsed[2].step)))

	if fitErr == None:
		fitErr = -5e3*numpy.ones(fitResults.shape, 'f')

	if startParams == None:
		startParams = -5e3*numpy.ones(fitResults.shape, 'f')

	tIndex = metadata.tIndex

	return numpy.array([(tIndex, fitResults.astype('f'), fitErr.astype('f'), resultCode, slicesUsed, startParams.astype('f'), nchi2)], dtype=fresultdtype)

		

def getDataErrors(im, metadata):
    dataROI = im - metadata.getEntry('Camera.ADOffset')

    return scipy.sqrt(metadata.getEntry('Camera.ReadNoise')**2 + (metadata.getEntry('Camera.NoiseFactor')**2)*metadata.getEntry('Camera.ElectronsPerCount')*metadata.getEntry('Camera.TrueEMGain')*dataROI)/metadata.getEntry('Camera.ElectronsPerCount')



class PSFFitFactory:
    def __init__(self, data, metadata, fitfcn=f_Interp3d2c, background=None):
        '''Create a fit factory which will operate on image data (data), potentially using voxel sizes etc contained in 
        metadata. '''
        self.data = data
        self.metadata = metadata
        self.background = background
        self.fitfcn = fitfcn #allow model function to be specified (to facilitate changing between accurate and fast exponential approwimations)
        if type(fitfcn) == types.FunctionType: #single function provided - use numerically estimated jacobian
            self.solver = FitModelWeighted_
        else: #should be a tuple containing the fit function and its jacobian
            self.solver = FitModelWeightedJac


        interpModule = metadata.Analysis.InterpModule
        self.interpolator = __import__('PYME.Analysis.FitFactories.Interpolators.' + interpModule , fromlist=['PYME', 'Analysis','FitFactories', 'Interpolators']).interpolator

        if fitfcn == f_Interp3d2c:
            if 'PSFFile' in metadata.getEntryNames():
                self.interpolator.setModel(metadata.PSFFile, metadata)
            else:
                self.interpolator.genTheoreticalModel(metadata)
		
        
    def __getitem__(self, key):
        xslice, yslice, zslice = key

        #cut region out of data stack
        dataROI = self.data[xslice, yslice, zslice] - self.metadata.Camera.ADOffset

        #generate grid to evaluate function on        
        Xg, Yg, Zg = self.interpolator.getCoords(self.metadata, xslice, yslice, zslice)


        #generate a corrected grid for the red channel
        #note that we're cheating a little here - for shifts which are slowly
        #varying we should be able to set Xr = Xg + delta_x(\bar{Xr}) and
        #similarly for y. For slowly varying shifts the following should be
        #equivalent to this. For rapidly varying shifts all bets are off ...

        #DeltaX, DeltaY = twoColour.getCorrection(Xg.mean(), Yg.mean(), self.metadata.chroma.dx,self.metadata.chroma.dy)
        x_ = Xg.mean() + (self.metadata.Camera.ROIPosX - 1)*1e3*self.metadata.voxelsize.x
        y_ = Yg.mean() + (self.metadata.Camera.ROIPosY - 1)*1e3*self.metadata.voxelsize.y
        DeltaX = self.metadata.chroma.dx.ev(x_, y_)
        DeltaY = self.metadata.chroma.dy.ev(x_, y_)

        Xr = Xg + DeltaX
        Yr = Yg + DeltaY
        Zr = Zg + self.metadata.Analysis.AxialShift

        #print DeltaX
        #print DeltaY

        #estimate some start parameters...
        Ag = dataROI[:,:,0].max() - dataROI[:,:,0].min() #amplitude
        Ar = dataROI[:,:,1].max() - dataROI[:,:,1].min() #amplitude



        x0 =  Xg.mean()
        y0 =  Yg.mean()
        z0 = 200.0

        #startParameters = [Ag, Ar, x0, y0, 250/2.35, dataROI[:,:,0].min(),dataROI[:,:,1].min(), .001, .001]

	
        #estimate errors in data
        nSlices = 1#dataROI.shape[2]
        
        #sigma = scipy.sqrt(self.metadata.CCD.ReadNoise**2 + (self.metadata.CCD.noiseFactor**2)*self.metadata.CCD.electronsPerCount*self.metadata.CCD.EMGain*dataROI)/self.metadata.CCD.electronsPerCount
        sigma = scipy.sqrt(self.metadata.Camera.ReadNoise**2 + (self.metadata.Camera.NoiseFactor**2)*self.metadata.Camera.ElectronsPerCount*self.metadata.Camera.TrueEMGain*scipy.maximum(dataROI, 1)/nSlices)/self.metadata.Camera.ElectronsPerCount


        if not self.background == None and len(numpy.shape(self.background)) > 1 and not ('Analysis.subtractBackground' in self.metadata.getEntryNames() and self.metadata.Analysis.subtractBackground == False):
            bgROI = self.background[xslice, yslice, zslice] - self.metadata.Camera.ADOffset

            dataROI = dataROI - bgROI

        startParameters = [Ag, Ar, x0, y0, z0, dataROI[:,:,0].min(),dataROI[:,:,1].min()]

        #print dataROI.shape
	
        #do the fit
        #(res, resCode) = FitModel(f_gauss2d, startParameters, dataMean, X, Y)
        #(res, cov_x, infodict, mesg, resCode) = FitModelWeighted(self.fitfcn, startParameters, dataMean, sigma, X, Y)
        (res, cov_x, infodict, mesg, resCode) = self.solver(self.fitfcn, startParameters, dataROI, sigma, self.interpolator,Xg, Yg, Zg, Xr, Yr, Zr)

        fitErrors=None
        try:       
            fitErrors = scipy.sqrt(scipy.diag(cov_x) * (infodict['fvec'] * infodict['fvec']).sum() / (len(dataROI.ravel())- len(res)))
        except Exception, e:
            pass

        #normalised Chi-squared
        nchi2 = (infodict['fvec']**2).sum()/(dataROI.size - res.size)

	#print res, fitErrors, resCode
        return PSFFitResultR(res, self.metadata, (xslice, yslice, zslice), resCode, fitErrors, numpy.array(startParameters), nchi2)

    def FromPoint(self, x, y, z=None, roiHalfSize=7, axialHalfSize=15):
        x = round(x)
        y = round(y)
	
        return self[max((x - roiHalfSize), 0):min((x + roiHalfSize + 1),self.data.shape[0]), 
                    max((y - roiHalfSize), 0):min((y + roiHalfSize + 1), self.data.shape[1]), 0:2]
        

#so that fit tasks know which class to use
FitFactory = PSFFitFactory
FitResult = PSFFitResultR
FitResultsDType = fresultdtype #only defined if returning data as numarray