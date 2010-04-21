#!/usr/bin/python

##################
# PsfFitIR.py
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

def f_Interp3d(p, interpolator, X, Y, Z, *args):
    """3D PSF model function with constant background - parameter vector [A, x0, y0, z0, background]"""
    A, x0, y0, z0, b = p

    #make sure our model is big enough to stretch to our current position
    xm = len(X)/2
    dx = min((interpolator.shape[0] - len(X))/2, xm) - 2

    ym = len(Y)/2
    dy = min((interpolator.shape[1] - len(Y))/2, ym) - 2


    x0 = min(max(x0, X[xm - dx]), X[dx + xm])
    y0 = min(max(y0, Y[ym - dy]), Y[dy + ym])
    z0 = min(max(z0, Z[0] + interpolator.IntZVals[2]), Z[0] + interpolator.IntZVals[-2])

    return interpolator.interp(X - x0 + 1, Y - y0 + 1, Z[0] - z0 + 1)*A + b


def replNoneWith1(n):
	if n == None:
		return 1
	else:
		return n



fresultdtype=[('tIndex', '<i4'),('fitResults', [('A', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('background', '<f4')]),('fitError', [('A', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('background', '<f4')]), ('resultCode', '<i4'), ('slicesUsed', [('x', [('start', '<i4'),('stop', '<i4'),('step', '<i4')]),('y', [('start', '<i4'),('stop', '<i4'),('step', '<i4')]),('z', [('start', '<i4'),('stop', '<i4'),('step', '<i4')])]), ('startParams', [('A', '<f4'),('x0', '<f4'),('y0', '<f4'),('z0', '<f4'), ('background', '<f4')]), ('nchi2', '<f4')]

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


def genFitImage(fitResults, metadata, fitfcn=f_Interp3d):
    if fitfcn == f_Interp3d:
        if 'PSFFile' in metadata.getEntryNames():
            setModel(metadata.getEntry('PSFFile'), metadata)
        else:
            genTheoreticalModel(metadata)

    xslice = slice(*fitResults['slicesUsed']['x'])
    yslice = slice(*fitResults['slicesUsed']['y'])

    X = 1e3*metadata.getEntry('voxelsize.x')*scipy.mgrid[xslice]
    Y = 1e3*metadata.getEntry('voxelsize.y')*scipy.mgrid[yslice]
    Z = array([0]).astype('f')
    P = scipy.arange(0,1.01,.01)

    im = fitfcn(fitResults['fitResults'], X, Y, Z, P).reshape(len(X), len(Y))

    return im

def getDataErrors(im, metadata):
    dataROI = im - metadata.getEntry('Camera.ADOffset')

    return scipy.sqrt(metadata.getEntry('Camera.ReadNoise')**2 + (metadata.getEntry('Camera.NoiseFactor')**2)*metadata.getEntry('Camera.ElectronsPerCount')*metadata.getEntry('Camera.TrueEMGain')*dataROI)/metadata.getEntry('Camera.ElectronsPerCount')

		

class PSFFitFactory:
    def __init__(self, data, metadata, fitfcn=f_Interp3d, background=None):
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

        if fitfcn == f_Interp3d:
            if 'PSFFile' in metadata.getEntryNames():
                self.interpolator.setModel(metadata.PSFFile, metadata)
            else:
                self.interpolator.genTheoreticalModel(metadata)
		
        
    def __getitem__(self, key):
        xslice, yslice, zslice = key

        #cut region out of data stack
        dataROI = self.data[xslice, yslice, zslice] - self.metadata.Camera.ADOffset

        #generate grid to evaluate function on        
        X, Y, Z = self.interpolator.getCoords(self.metadata, xslice, yslice, zslice)

        #estimate some start parameters...
        A = dataROI.max() - dataROI.min() #amplitude

        

        x0 =  X.mean()
        y0 =  Y.mean()
        z0 = 200.0

        startParameters = [A, x0, y0, z0, dataROI.min()]


        #estimate errors in data
        nSlices = 1#dataROI.shape[2]

        sigma = scipy.sqrt(self.metadata.Camera.ReadNoise**2 + (self.metadata.Camera.NoiseFactor**2)*self.metadata.Camera.ElectronsPerCount*self.metadata.Camera.TrueEMGain*dataROI)/self.metadata.Camera.ElectronsPerCount

        #do the fit
        (res, cov_x, infodict, mesg, resCode) = self.solver(self.fitfcn, startParameters, dataROI, sigma, self.interpolator, X, Y, Z)

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