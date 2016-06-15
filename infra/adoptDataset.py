#!/usr/bin/python

import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.utils as imu

#################
### CONSTANTS ###
#################
currentSymlink = 'current'
newSymlink = 'new'

############
### MAIN ###
############
parser = imu.ArgParser('Adopt the given dataset for loading into InterMine')
parser.add_argument('datasetPath', help='path for the dataset')
parser.add_argument('minePath', help='path to the mine')
args = parser.parse_args()

dsPath = args.datasetPath
minePath = args.minePath

dsProjectXmlPath = '%s/intermine/project.xml' % (dsPath)
mineProjectXmlPath = '%s/project.xml' % (minePath)
shutil.copy(dsProjectXmlPath, mineProjectXmlPath)

dsCurrentSymlink = '%s/%s' % (dsPath, currentSymlink)
dsNewSymlink = '%s/%s' % (dsPath, newSymlink)

if os.path.islink(dsPath):
    realDsPath = os.readlink(dsPath)
else:
    realDsPath = dsPath

os.chdir('%s/..' % dsPath)
os.remove(currentSymlink)
os.remove(newSymlink)
os.symlink(os.path.basename(realDsPath), currentSymlink)