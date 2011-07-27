#!/usr/bin/python
##################
# richardsonLucy.py
#
# Copyright David Baddeley, 2011
# d.baddeley@auckland.ac.nz
# 
# This file may NOT be distributed without express permision from David Baddeley
#
##################
from scipy import *
from scipy.linalg import *
#from scipy.fftpack import fftn, ifftn, fftshift, ifftshift
from scipy import ndimage
import numpy
from scipy.fftpack import fftn, ifftn, fftshift, ifftshift
import fftw3f
#import weave
#import cDec
from PYME import pad
#import dec

class rldec:
    '''Deconvolution class, implementing a variant of the Richardson-Lucy algorithm.

    Derived classed should additionally define the following methods:
    AFunc - the forward mapping (computes Af)
    AHFunc - conjugate transpose of forward mapping (computes \bar{A}^T f)
    LFunc - the likelihood function
    LHFunc - conj. transpose of likelihood function

    see dec_conv for an implementation of conventional image deconvolution with a
    measured, spatially invariant PSF
    '''
    def __init__(self):
       pass

    def startGuess(self, data):
        '''starting guess for deconvolution - can be overridden in derived classes
        but the data itself is usually a pretty good guess.
        '''
        return 0*data + data.mean()


    def deconv(self, data, lamb, num_iters=10, alpha = None):
        '''This is what you actually call to do the deconvolution.
        parameters are:

        data - the raw data
        lamb - the regularisation parameter
        num_iters - number of iterations (note that the convergence is fast when
                    compared to many algorithms - e.g Richardson-Lucy - and the
                    default of 10 will usually already give a reasonable result)

        alpha - PSF phase - hacked in for variable phase 4Pi deconvolution, should
                really be refactored out into the dec_4pi classes.
        '''
        #remember what shape we are
        self.dataShape = data.shape

        #guess a starting estimate for the object
        self.f = self.startGuess(data)

        #make things 1 dimensional
        self.f = self.f.ravel()
        data = data.ravel()

        self.loopcount=0

        for self.loopcount in range(num_iters):
            

            #the residuals
            self.res = data/self.Afunc(self.f);

            print 'Residual norm = %f' % norm(self.res)

            #adjustment
            adjFact = self.Ahfunc(self.res)

            fnew = self.f*adjFact


            #set the current estimate to out new estimate
            self.f = fnew

        return real(self.f)

#class rlbead(rl):
class rlbead(rldec):
    '''Classical deconvolution using non-fft convolution - pot. faster for
    v. small psfs. Note that PSF must be symetric'''
    def psf_calc(self, psf, data_size):
        g = psf#/psf.sum();

        #keep track of our data shape
        self.height = data_size[0]
        self.width  = data_size[1]
        self.depth  = data_size[2]

        self.shape = data_size

        self.g = g;

        #calculate OTF and conjugate transformed OTF
        #self.H = (fftn(g));
        #self.Ht = g.size*(ifftn(g));

    def Afunc(self, f):
        '''Forward transform - convolve with the PSF'''
        fs = reshape(f, (self.height, self.width, self.depth))

        d = ndimage.convolve(fs, self.g)

        #d = real(d);
        return ravel(d)

    def Ahfunc(self, f):
        '''Conjugate transform - convolve with conj. PSF'''
        fs = reshape(f, (self.height, self.width, self.depth))

        d = ndimage.correlate(fs, self.g)

        return ravel(d)

class dec_conv_slow(rldec):
    '''Classical deconvolution with a stationary PSF'''
    def psf_calc(self, psf, data_size):
        '''Precalculate the OTF etc...'''
        pw = (numpy.array(data_size) - psf.shape)/2.
        pw1 = numpy.floor(pw)
        pw2 = numpy.ceil(pw)

        g = psf/psf.sum()

        #work out how we're going to need to pad to get the PSF the same size as our data
        if pw1[0] < 0:
            if pw2[0] < 0:
                g = g[-pw1[0]:pw2[0]]
            else:
                g = g[-pw1[0]:]

            pw1[0] = 0
            pw2[0] = 0

        if pw1[1] < 0:
            if pw2[1] < 0:
                g = g[-pw1[1]:pw2[1]]
            else:
                g = g[-pw1[1]:]

            pw1[1] = 0
            pw2[1] = 0

        if pw1[2] < 0:
            if pw2[2] < 0:
                g = g[-pw1[2]:pw2[2]]
            else:
                g = g[-pw1[2]:]

            pw1[2] = 0
            pw2[2] = 0


        #do the padding
        g = pad.with_constant(g, ((pw2[0], pw1[0]), (pw2[1], pw1[1]),(pw2[2], pw1[2])), (0,))


        #keep track of our data shape
        self.height = data_size[0]
        self.width  = data_size[1]
        self.depth  = data_size[2]

        self.shape = data_size

        self.g = g;

        #calculate OTF and conjugate transformed OTF
        self.H = (fftn(g));
        self.Ht = g.size*(ifftn(g));


    def Lfunc(self, f):
        '''convolve with an approximate 2nd derivative likelihood operator in 3D.
        i.e. [[[0,0,0][0,1,0][0,0,0]],[[0,1,0][1,-6,1][0,1,0]],[[0,0,0][0,1,0][0,0,0]]]
        '''
        #make our data 3D again
        fs = reshape(f, (self.height, self.width, self.depth))
        a = -6*fs

        a[:,:,0:-1] += fs[:,:,1:]
        a[:,:,1:] += fs[:,:,0:-1]

        a[:,0:-1,:] += fs[:,1:,:]
        a[:,1:,:] += fs[:,0:-1,:]

        a[0:-1,:,:] += fs[1:,:,:]
        a[1:,:,:] += fs[0:-1,:,:]

        #flatten data again
        return ravel(cast['f'](a))

    Lhfunc=Lfunc

    def Afunc(self, f):
        '''Forward transform - convolve with the PSF'''
        fs = reshape(f, (self.height, self.width, self.depth))

        F = fftn(fs)

        d = ifftshift(ifftn(F*self.H));

        d = real(d);
        return ravel(d)

    def Ahfunc(self, f):
        '''Conjugate transform - convolve with conj. PSF'''
        fs = reshape(f, (self.height, self.width, self.depth))

        F = fftn(fs)
        d = ifftshift(ifftn(F*self.Ht));
        d = real(d);
        return ravel(d)

class dec_conv(rldec):
    '''Classical deconvolution with a stationary PSF'''
    def psf_calc(self, psf, data_size):
        '''Precalculate the OTF etc...'''
        pw = (numpy.array(data_size) - psf.shape)/2.
        pw1 = numpy.floor(pw)
        pw2 = numpy.ceil(pw)

        g = psf/psf.sum()

        #work out how we're going to need to pad to get the PSF the same size as our data
        if pw1[0] < 0:
            if pw2[0] < 0:
                g = g[-pw1[0]:pw2[0]]
            else:
                g = g[-pw1[0]:]

            pw1[0] = 0
            pw2[0] = 0

        if pw1[1] < 0:
            if pw2[1] < 0:
                g = g[-pw1[1]:pw2[1]]
            else:
                g = g[-pw1[1]:]

            pw1[1] = 0
            pw2[1] = 0

        if pw1[2] < 0:
            if pw2[2] < 0:
                g = g[-pw1[2]:pw2[2]]
            else:
                g = g[-pw1[2]:]

            pw1[2] = 0
            pw2[2] = 0


        #do the padding
        g = pad.with_constant(g, ((pw2[0], pw1[0]), (pw2[1], pw1[1]),(pw2[2], pw1[2])), (0,))


        #keep track of our data shape
        self.height = data_size[0]
        self.width  = data_size[1]
        self.depth  = data_size[2]

        self.shape = data_size

        FTshape = [self.shape[0], self.shape[1], self.shape[2]/2 + 1]

        self.g = g.astype('f4');
        self.g2 = 1.0*self.g[::-1, ::-1, ::-1]

        #allocate memory
        self.H = fftw3f.create_aligned_array(FTshape, 'complex64')
        self.Ht = fftw3f.create_aligned_array(FTshape, 'complex64')
        #self.f = zeros(self.shape, 'f4')
        #self.res = zeros(self.shape, 'f4')
        #self.S = zeros((size(self.f), 3), 'f4')

        self._F = fftw3f.create_aligned_array(FTshape, 'complex64')
        self._r = fftw3f.create_aligned_array(self.shape, 'f4')
        #S0 = self.S[:,0]

        #create plans & calculate OTF and conjugate transformed OTF
        fftw3f.Plan(self.g, self.H, 'forward')()
        fftw3f.Plan(self.g2, self.Ht, 'forward')()

        self.Ht /= g.size;
        self.H /= g.size;

        #calculate plans for other ffts
        self._plan_r_F = fftw3f.Plan(self._r, self._F, 'forward')
        self._plan_F_r = fftw3f.Plan(self._F, self._r, 'backward')


    def Lfunc(self, f):
        '''convolve with an approximate 2nd derivative likelihood operator in 3D.
        i.e. [[[0,0,0][0,1,0][0,0,0]],[[0,1,0][1,-6,1][0,1,0]],[[0,0,0][0,1,0][0,0,0]]]
        '''
        #make our data 3D again
        fs = reshape(f, (self.height, self.width, self.depth))
        a = -6*fs

        a[:,:,0:-1] += fs[:,:,1:]
        a[:,:,1:] += fs[:,:,0:-1]

        a[:,0:-1,:] += fs[:,1:,:]
        a[:,1:,:] += fs[:,0:-1,:]

        a[0:-1,:,:] += fs[1:,:,:]
        a[1:,:,:] += fs[0:-1,:,:]

        #flatten data again
        return ravel(cast['f'](a))

    Lhfunc=Lfunc

    def Afunc(self, f):
        '''Forward transform - convolve with the PSF'''
        #fs = reshape(f, (self.height, self.width, self.depth))
        self._r[:] = f.reshape(self._r.shape)

        #F = fftn(fs)

        #d = ifftshift(ifftn(F*self.H));
        self._plan_r_F()
        self._F *= self.H
        self._plan_F_r()

        #d = real(d);
        return ravel(ifftshift(self._r))

    def Ahfunc(self, f):
        '''Conjugate transform - convolve with conj. PSF'''
#        fs = reshape(f, (self.height, self.width, self.depth))
#
#        F = fftn(fs)
#        d = ifftshift(ifftn(F*self.Ht));
#        d = real(d);
#        return ravel(d)
        self._r[:] = f.reshape(self._r.shape)

        self._plan_r_F()
        self._F *= self.Ht
        self._plan_F_r()

        return ravel(ifftshift(self._r))