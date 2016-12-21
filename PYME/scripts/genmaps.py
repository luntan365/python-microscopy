import sys
import argparse
import numpy as np
import PYME.IO.image as im
import PYME.IO.dataExporter as dexp
from PYME.IO.MetaDataHandler import NestedClassMDHandler

def saveasmap(array,filename,mdh=None):
    array.shape += (1,) * (4 - array.ndim) # ensure we have trailing dims making up to 4D
    dexp.ExportData(array,mdh,filename=filename)

def meanvards(dataSource, start=0, end=-1):

    nslices = dataSource.getNumSlices()
    if end < 0:
        end = nslices + end

    nframes = end - start
    xSize, ySize = dataSource.getSliceShape()

    m = np.zeros((xSize,ySize),dtype='float64')
    for frameN in range(start,end):
        m += dataSource.getSlice(frameN)
    m = m / nframes

    v = np.zeros((xSize,ySize),dtype='float64')
    for frameN in range(start,end):
        v += (dataSource.getSlice(frameN)-m)**2
    v = v / (nframes-1)

    return (m,v)

import os
import errno
def makePathUnlessExists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def mkDestPath(destdir,stem,mdh):
    if not os.path.isdir(destdir):
        raise ValueError('directory %s does not exist; please create' % destdir)
    itime = int(1000*mdh['Camera.IntegrationTime'])
    return os.path.join(destdir,'%s_%dms.tif' % (stem,itime))

from PYME.IO.FileUtils import nameUtils
def mkDefaultPath(stem,mdh):
   caldir = nameUtils.getCalibrationDir(mdh['Camera.SerialNumber'])
   makePathUnlessExists(caldir)
   return mkDestPath(caldir,stem,mdh)

import os
from glob import glob
def listCalibrationDirs():
    rootdir = nameUtils.getCalibrationDir('')
    result = [y for x in os.walk(rootdir) for y in glob(os.path.join(x[0], '*.tif'))]
    if result is not None:
        print 'List of installed maps:'
        for m in result:
            print m

# options parsing
op = argparse.ArgumentParser(description='generate offset and variance maps from darkseries.')
op.add_argument('filename', metavar='filename', nargs='?', default=None,
                help='filename of the darkframe series')
op.add_argument('-s', '--start', type=int, default=0, 
                help='start frame to use')
op.add_argument('-e', '--end', type=int, default=-1, 
                help='end frame to use')
op.add_argument('-d', '--dir', metavar='destdir', default=None,
                help='destination directory (default is PYME calibration path)')
#op.add_argument('-i','--install', action='store_true',
#                help='install in default location, overrides --postfix')
op.add_argument('-l','--list', action='store_true',
                help='list all maps in default location')


args = op.parse_args()

if args.list:
    listCalibrationDirs()
    sys.exit(0)

# body of script
filename = args.filename

if filename is None:
    op.error('need a file name if -l or --list not requested')

print >> sys.stderr, 'Opening image series...'
st = im.ImageStack(filename=filename)

start = args.start
end = args.end
if end < 0:
    end = int(st.dataSource.getNumSlices() + end)

print >> sys.stderr, 'Calculating mean and variance...'
m, v = meanvards(st.dataSource, start = start, end=end)
eperADU = st.mdh['Camera.ElectronsPerCount']
ve = v*eperADU*eperADU

print >> sys.stderr, 'Saving results...'

if args.dir is None:
    print >> sys.stderr, 'installing in standard location...'
    mname = mkDefaultPath('dark',st.mdh)
    vname = mkDefaultPath('variance',st.mdh)
else:
    mname = mkDestPath(args.dir,'dark',st.mdh)
    vname = mkDestPath(args.dir,'variance',st.mdh)

print  >> sys.stderr, 'dark map -> %s...' % mname
print  >> sys.stderr, 'var  map -> %s...' % vname

mmd = NestedClassMDHandler()
mmd.copyEntriesFrom(st.mdh)
#mmd.Source = NestedClassMDHandler(st.mdh)

mmd.setEntry('Analysis.name', 'mean-variance')
mmd.setEntry('Analysis.resultname', 'mean')
mmd.setEntry('Analysis.start', start)
mmd.setEntry('Analysis.end', end)
mmd.setEntry('Analysis.units', 'ADU')
mmd.setEntry('Analysis.Source.Filename', filename)

vmd = NestedClassMDHandler()
#vmd.Source = NestedClassMDHandler(st.mdh)
vmd.copyEntriesFrom(st.mdh)

mmd.setEntry('Analysis.name', 'mean-variance')
mmd.setEntry('Analysis.resultname', 'variance')
vmd.setEntry('Analysis.start', start)
vmd.setEntry('Analysis.end', end)
vmd.setEntry('Analysis.units', 'electrons^2')
vmd.setEntry('Analysis.Source.Filename', filename)

saveasmap(m,mname,mdh=mmd)
saveasmap(ve,vname,mdh=vmd)
