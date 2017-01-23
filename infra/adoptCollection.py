#!/usr/bin/env python3

import jargparse
import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import synbio.data as sbd

#################
### CONSTANTS ###
#################
currentSymlink = 'current'
toAdoptSymlink = 'new'

############
### MAIN ###
############
parser = jargparse.ArgParser('Adopt the given data collection for loading into InterMine.  If the data collection is already the current, then the files are just updated instead.')
parser.add_argument('colPath', help='path to the data collection')
parser.add_argument('minePath', help='path to the mine')
args = parser.parse_args()

# FIXME: We need to fix logging here - this is currently tied to datasets but these infrastructure scripts have no
# dataset.  Either change the logging architecture or possible give infra a 'dummy' dataset
colPath = args.colPath
minePath = args.minePath

# copy general config files
dsProjectXmlPath = '%s/intermine/project.xml' % (colPath)
mineProjectXmlPath = '%s/project.xml' % (minePath)
shutil.copy(dsProjectXmlPath, mineProjectXmlPath)

# copy the generated synbis additions file.  If we do this for other sets then at some point this mechanism will have to
# be generalized
dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
shutil.copy(ds.getProcessingPath() + 'synbio-synbis_additions.xml', minePath + '/../bio/sources/synbio/synbio-synbis/synbio-synbis_additions.xml')

# update symlink if appropriate
toAdoptColPath = os.path.realpath('%s/../%s' % (colPath, toAdoptSymlink))
currentColPath = os.path.realpath('%s/../%s' % (colPath, currentSymlink))

if os.path.realpath(colPath) != currentColPath:
    os.chdir('%s/..' % colPath)
    os.remove(currentSymlink)
    os.remove(toAdoptSymlink)
    os.symlink(os.path.basename(toAdoptColPath), currentSymlink)
    print('Adopted dataset %s to %s' % (toAdoptColPath, currentSymlink))
else:
    print('Updated files on already adopted dataset %s' % currentColPath)
