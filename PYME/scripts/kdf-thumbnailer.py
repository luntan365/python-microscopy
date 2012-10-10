#!/usr/bin/python

##################
# kdf-thumbnailer.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##################

#!/usr/bin/python

import sys
#import gnomevfs

#import tables

#from PYME.Analysis.LMVis import inpFilt
from scipy import minimum, maximum
import Image

from PYME import cSMI

#from PYME.Analysis import MetaData
#from PYME.Acquire import MetaDataHandler
#from PYME.Analysis.DataSources import HDFDataSource

#import logging
#LOG_FILENAME = '/tmp/h5r-thumbnailer.log'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)

#print sys.argv
#inputFile = gnomevfs.get_local_path_from_uri(sys.argv[1])
#outputFile = sys.argv[2]
#thumbSize = int(sys.argv[3])

#logging.debug('Input File: %s\n' % inputFile)
#logging.debug('Ouput File: %s\n' % outputFile)
#logging.debug('Thumb Size: %s\n' % thumbSize)

size=(200,200)

def generateThumbnail(inputFile, thumbSize):
    global size
    im = cSMI.CDataStack_AsArray(cSMI.CDataStack(inputFile.encode()), 0).mean(2).squeeze()


    xsize = im.shape[0]
    ysize = im.shape[1]

    if xsize > ysize:
        zoom = float(thumbSize)/xsize
    else:
        zoom = float(thumbSize)/ysize

    size = (int(xsize*zoom), int(ysize*zoom))

    im = im - im.min()

    im = maximum(minimum(1*(255*im)/im.max(), 255), 0)

    return im.astype('uint8')


if __name__ == '__main__':
    import gnomevfs
    inputFile = gnomevfs.get_local_path_from_uri(sys.argv[1])
    outputFile = sys.argv[2]
    thumbSize = int(sys.argv[3])

    im = generateThumbnail(inputFile, thumbSize)

    Image.fromarray(im).resize(size).save(outputFile, 'PNG')
