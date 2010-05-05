from scipy import ndimage
import numpy
import binAvg

def imageDensityAtDistance(A, mask, voxelsize = None, bins=100):
    '''Calculates the distribution of a label at varying distances from a mask.
    Negative distances are on the inside of the mask.

    Parameters:
    A - intensity image
    mask - binary mask
    voxelsize - size of the pixels/voxels - should be either a constant, or an iterable
                with a length equal to the number of dimensions in the data
    bins - either a number of bins, or an array of bin edges


    Returns:
    bn - integrated intensity in distance bin
    bm - mean intensity in distance bin
    bins - the bin edges
    '''
    
    if voxelsize == None:
        voxelsize = numpy.ones(len(A.shape))

    dt = -ndimage.distance_transform_edt(mask, sampling=voxelsize)

    dt = dt + ndimage.distance_transform_edt(ndimage.binary_dilation(1-mask), sampling=voxelsize)

    if numpy.isscalar(bins):
        bins = numpy.linspace(dt.min(), dt.max(), bins+1)

    bn, bm, bs = binAvg.binAvg(dt, A, bins)

    return bn, bm, bins


def pointDensityAtDistance(points, mask, voxelsize, maskOffset, bins=100):
    '''Calculates the distribution of a label at varying distances from a mask.
    Negative distances are on the inside of the mask.

    Parameters:
    points - array containing point coordinates
    mask - binary mask
    voxelsize - size of the pixels/voxels in mask - should be an iterable
                with a length equal to the number of dimensions in the data
    maskOffset - iterable with lengh equal to number of dims giving coordinates (in point space)
                 or the 0th pixel in the mask
    bins - either a number of bins, or an array of bin edges


    Returns:
    bn - integrated intensity in distance bin
    bm - mean intensity in distance bin
    bins - the bin edges
    '''

    voxelsize = numpy.array(voxelsize)

    dt = -ndimage.distance_transform_edt(mask, sampling=voxelsize)

    dt = dt + ndimage.distance_transform_edt(ndimage.binary_dilation(1-mask), sampling=voxelsize)

    pixelCoords = numpy.round((points - maskOffset[None, :])/[voxelsize[None, :]]).astype('i')

    dists = dt[pixelCoords]


    if numpy.isscalar(bins):
        bins = numpy.linspace(dt.min(), dt.max(), bins+1)

    n_events, b = numpy.histogram(dists, bins)
    n_pixels, b = numpy.histogram(dt.flat, bins)

    ev_density = n_events/n_pixels
    ev_density[n_pixels ==0] = 0

    return n_events, ev_density, bins


