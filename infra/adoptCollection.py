#!/usr/bin/python

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
newSymlink = 'new'

############
### MAIN ###
############
parser = jargparse.ArgParser('Adopt the given data collection for loading into InterMine')
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
shutil.copy(ds.getProcessingPath() + 'synbio-synbis_additions.xml', minePath + '/bio/sources/synbio/synbio-synbis/synbio-synbis_additions.xml')

# update symlink
dsCurrentSymlink = '%s/%s' % (colPath, currentSymlink)
dsNewSymlink = '%s/%s' % (colPath, newSymlink)

if os.path.islink(colPath):
    realDsPath = os.readlink(colPath)
else:
    realDsPath = colPath

os.chdir('%s/..' % colPath)
os.remove(currentSymlink)
os.remove(newSymlink)
os.symlink(os.path.basename(realDsPath), currentSymlink)

print('Adopted dataset')