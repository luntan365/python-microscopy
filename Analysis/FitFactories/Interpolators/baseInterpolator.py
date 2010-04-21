from numpy import *
from PYME.ParallelTasks.relativeFiles import getFullExistingFilename

class __interpolator:
    def __init__(self):
        self.IntXVals = None
        self.IntYVals = None
        self.IntZVals = None

        self.interpModel = None
        self.interpModelName = None

        self.dx = None
        self.dy = None
        self.dz = None

    def setModel(self, modName, md):
        '''load the model from file'''
        #global IntXVals, IntYVals, IntZVals, interpModel, interpModelName, dx, dy, dz

        if not modName == self.interpModelName:
            mf = open(getFullExistingFilename(modName), 'rb')
            mod, voxelsize = cPickle.load(mf)
            mf.close()

            self.interpModelName = modName

            #if not voxelsize.x == md.voxelsize.x:
            #    raise RuntimeError("PSF and Image voxel sizes don't match")

            self. IntXVals = 1e3*voxelsize.x*mgrid[-(mod.shape[0]/2.):(mod.shape[0]/2.)]
            self.IntYVals = 1e3*voxelsize.y*mgrid[-(mod.shape[1]/2.):(mod.shape[1]/2.)]
            self.IntZVals = 1e3*voxelsize.z*mgrid[-(mod.shape[2]/2.):(mod.shape[2]/2.)]

            self.dx = voxelsize.x*1e3
            self.dy = voxelsize.y*1e3
            self.dz = voxelsize.z*1e3

            self.interpModel = mod/mod.max() #normalise to 1
            self.shape = mod.shape

            self._precompute()

    def genTheoreticalModel(self, md):
        from PYME.PSFGen.ps_app import *

        if not self.dx == md.voxelsize.x*1e3 and not self.dy == md.voxelsize.y*1e3 and not self.dz == md.voxelsize.z*1e3:

            self.IntXVals = 1e3*md.voxelsize.x*mgrid[-20:20]
            self.IntYVals = 1e3*md.voxelsize.y*mgrid[-20:20]
            self.IntZVals = 1e3*md.voxelsize.z*mgrid[-20:20]

            self.dx = md.voxelsize.x*1e3
            self.dy = md.voxelsize.y*1e3
            self.dz = md.voxelsize.z*1e3

            P = arange(0,1.01,.01)

            interpModel = genWidefieldPSF(self.IntXVals, self.IntYVals, self.IntZVals, P,1e3, 0, 0, 0, 2*pi/525, 1.47, 10e3)

            self.interpModel = interpModel/interpModel.max() #normalise to 1

            self.shape = interpModel.shape

            self._precompute()

    def _precompute(self):
        '''placeholder function which is called after model loading and can be
        overridden to allow for interpolation specific precomputations'''
        pass

    def interp(self, X, Y, Z):
        '''placeholder to be overrriden to do actual interpolation at values given'''
        raise RuntimeError('Not Implemented')

    def getCoords(self, metadata, xslice, yslice, zslice):
        '''placeholder to be overrriden to return coordinates needed for interpolation'''
        raise RuntimeError('Not Implemented')
