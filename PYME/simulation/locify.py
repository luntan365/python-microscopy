#!/usr/bin/python

##################
# locify.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
# Generates a series of point/fluorophore positions from a given grayscale image
#
##################

from numpy.random import rand
import numpy as np
#import np.random


def locify(im, pixelSize=1, pointsPerPixel=0.1):
    '''Create a set of point positions with a density corresponding to the
    input image im. Useful for generating localisation microscopy images from
    conventional images. Assumes im is a 2D array with values between 0 and 1
    and interprets this value as a probability. pointsPerPixel gives the point density for a prob. of 1.'''
    
    im = np.atleast_3d(im)

    #what range shold we generate points in
    xmax = im.shape[0]
    ymax = im.shape[1]
    zmax = im.shape[2]

    #generate a number of candidate points based on uniform labelling
    #which will be accepted/rejected later
    numPoints = int(xmax*ymax*zmax*pointsPerPixel)

    x = xmax*rand(numPoints) - .5
    y = ymax*rand(numPoints) - .5
    z = zmax*rand(numPoints) - .5
    
    #print len(x)

    #index into array to get probability of acceptance
    p = im[x.round().astype('i'), y.round().astype('i'), z.round().astype('i')]

    #use monte-carlo to accept points with the given probability
    mcInd = rand(len(x)) < p.ravel()

    #print x.shape, mcInd.shape, p.shape, rand(len(x)).shape

    #take subset of positions and scale to pixel size
    x = pixelSize*x[mcInd]
    y = pixelSize*y[mcInd]
    z = pixelSize * z[mcInd]

    return (x,y,z)
    

def testPattern():
    '''generate a test pattern'''
    pass
    
fresultdtype=[('tIndex', '<i4'),
              ('fitResults', [('A', '<f4'),('x0', '<f4'),('y0', '<f4'), ('z0', '<f4'),('sigma', '<f4')]),
              ('fitError', [('A', '<f4'),('x0', '<f4'),('y0', '<f4'), ('z0', '<f4'),('sigma', '<f4')])]


_s2 = 110.**2
_a2 = 70.**2

_s2_a2_12 = _s2 + _a2/12
_8_pi_s2_2_a2 = (8*np.pi*_s2**2)/_a2
_r_2_pi = 1.0/2*np.pi

def FitResultR(x,y,z,I,t, b2, z_err_mult=3):
    r_I = np.sqrt(I)
        
    s2 = 110**2
    a2 = 70**2
    
    err_x = np.sqrt((s2 + a2/12)/I + 8*np.pi*s2**2*b2/(a2*I**2))
    err_z = z_err_mult*err_x

    return np.array([(t, np.array([I/(2*np.pi), x, y, z, 110.], 'f'), np.array([r_I/(2*np.pi), err_x, err_x, err_z, err_x], 'f'))], dtype=fresultdtype)

def _eventify(x,y,meanIntensity, meanDuration, backGroundIntensity, meanEventNumber, sf = 2, tm=2000, z=0, z_err_scale=1.0):
    Is = np.random.exponential(meanIntensity, x.shape)
    Ns = np.random.poisson(meanEventNumber, x.shape)
    
    if np.isscalar(z):
        z = z*np.ones_like(x)
    
    evts = []
    #t = 0

    for x_i, y_i, z_i, I_i, N_i in zip(x,y, z,Is,Ns):
        for j in range(N_i):
            duration = np.random.exponential(meanDuration)
            t = np.random.exponential(tm)

            #evts += [(x_i, y_i, I_i, t+k) for k in range(duration)] + [(x_i, y_i, I_i*(duration%1), t+floor(duration))]
            evts.extend([FitResultR(x_i, y_i, z_i, I_i, t+k, backGroundIntensity, z_err_mult=z_err_scale) for k in range(int(np.floor(duration)))])
            evts.append(FitResultR(x_i, y_i, z_i, I_i*(duration%1), t+np.floor(duration), backGroundIntensity, z_err_mult=z_err_scale))

    evts = np.vstack(evts)
    
    #xn, yn, In = evts[:,0], evts[:,1], evts[:,2]

    In = evts['fitResults']['A']

    detect = np.exp(-(In)**2/(2*sf**2*backGroundIntensity)) < np.random.uniform(size=In.shape)

    #xn = xn[detect]
    #yn = yn[detect]
    #In = In[detect]

    evts = evts[detect]

    s = evts['fitResults']['x0'].shape

    evts['fitResults']['x0'] = evts['fitResults']['x0'] + evts['fitError']['x0']*np.random.normal(size=s)
    evts['fitResults']['y0'] = evts['fitResults']['y0'] + evts['fitError']['y0']*np.random.normal(size=s)
    evts['fitResults']['z0'] = evts['fitResults']['z0'] + evts['fitError']['z0']*np.random.normal(size=s)

    #filter

    return evts

def eventify(*args, **kwargs):
    return eventify2(*args, paint_mode=False, **kwargs)


def eventify2(x, y, meanIntensity, meanDuration, backGroundIntensity, meanEventNumber, sf=2, tm=10000, z=0,
             z_err_scale=1.0, paint_mode=True):
    """ PAINT version of eventify """
    
    
    #Is =
    Ns = np.random.poisson(meanEventNumber, x.shape)

    if np.isscalar(z):
        z = z * np.ones_like(x)

    evts = []
    #t = 0

    for x_i, y_i, z_i, N_i in zip(x, y, z, Ns):
        duration = np.random.exponential(meanDuration, size=N_i)
        n_frames = np.ceil(duration).astype('i')
        
        if paint_mode:
            Is = np.random.exponential(meanIntensity, size=N_i)
            ts = 2*tm*np.random.uniform(size=N_i)
        else:
            Is = np.random.exponential(meanIntensity)*np.ones(N_i)
            ts = np.random.exponential(tm, size=N_i)
        
        evts_i = np.empty(n_frames.sum(), dtype=fresultdtype)
        
        evts_i['fitResults']['x0'] = x_i
        evts_i['fitResults']['y0'] = y_i
        evts_i['fitResults']['z0'] = z_i
        
        k = 0
        
        for j in range(N_i):
            k2 = k + n_frames[j]
            evts_i['fitResults']['A'][k:k2] = Is[j]
            evts_i['fitResults']['A'][k2-1] = Is[j]*(duration[j] %1)
            evts_i['tIndex'][k:k2] = ts[j]+np.arange(n_frames[j])
            
            k = k2
            
            #n_frames = int(np.ceil(duration[j]))
            #t = 2*tm*np.random.uniform()
            
            #I_i = np.random.exponential(meanIntensity)
            
            #t_i = ts[j]+np.arange(n_frames[j])
            
            #I_i = Is[j]*np.ones(n_frames[j])
            #I_i[-1] = I_i[-1]*(duration[j] %1)
        
            #evts += [(x_i, y_i, I_i, t+k) for k in range(duration)] + [(x_i, y_i, I_i*(duration%1), t+floor(duration))]
            #evts.extend([FitResultR(x_i, y_i, z_i, I_i, t + k, backGroundIntensity, z_err_mult=z_err_scale) for k in
            #             range(int(np.floor(duration)))])
            #evts.append(FitResultR(x_i, y_i, z_i, I_i, t_i, backGroundIntensity, z_err_mult=z_err_scale))
        evts.append(evts_i)

    evts = np.hstack(evts)

    #xn, yn, In = evts[:,0], evts[:,1], evts[:,2]
    
    

    In = evts['fitResults']['A']*_r_2_pi

    detect = np.exp(-(In) ** 2 / (2 * sf ** 2 * backGroundIntensity)) < np.random.uniform(size=In.shape)

    #xn = xn[detect]
    #yn = yn[detect]
    #In = In[detect]

    evts = evts[detect]
    
    I = evts['fitResults']['A']

    err_x = np.sqrt(_s2_a2_12 / I + _8_pi_s2_2_a2 * backGroundIntensity / (I * I))
    evts['fitError']['x0'] = err_x

    evts['fitResults']['A'] = I*_r_2_pi
    evts['fitError']['A'] = np.sqrt(I) * _r_2_pi
    
    
    evts['fitError']['x0'] =err_x
    evts['fitError']['y0'] = err_x
    evts['fitError']['z0'] = z_err_scale*err_x

    #fill in the things we don't really need.
    evts['fitResults']['sigma'] = 110.
    evts['fitError']['sigma'] = err_x

    s = evts['fitResults']['x0'].shape

    evts['fitResults']['x0'] = evts['fitResults']['x0'] + evts['fitError']['x0'] * np.random.normal(size=s)
    evts['fitResults']['y0'] = evts['fitResults']['y0'] + evts['fitError']['y0'] * np.random.normal(size=s)
    evts['fitResults']['z0'] = evts['fitResults']['z0'] + evts['fitError']['z0'] * np.random.normal(size=s)

    #filter

    return evts

    #return xn, yn, In