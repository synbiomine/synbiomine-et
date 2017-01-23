#!/usr/bin/env python3

import jargparse
import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.utils as imu

#################
### CONSTANTS ###
#################
sections = [ 'eggnog', 'genbank', 'goa', 'intermine', 'kegg', 'taxons', 'uniprot' ]
logsDir = 'logs'
newDatasetSymlink = '../new'

############
### MAIN ###
############
parser = jargparse.ArgParser('Prepare a new data collection in the data repository')
parser.add_argument('modelPath', help='path to the mine model XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

modelPath = args.modelPath
colPath = args.colPath
newDatasetSymlinkPath = "%s/%s" % (colPath, newDatasetSymlink)

if os.path.exists(colPath):
    raise Exception("Dataset path %s already exists!" % colPath)

os.mkdir(colPath)
os.mkdir("%s/%s" % (colPath, logsDir))

for section in sections:
    sectionPath = "%s/%s" % (colPath, section)
    os.mkdir(sectionPath)

datasetModelPath = "%s/intermine/genomic_model.xml" % colPath
shutil.copy(modelPath, datasetModelPath)

os.symlink(os.path.basename(colPath), newDatasetSymlinkPath)

print('Created dataset structure at %s, symlinked %s' % (colPath, newDatasetSymlink))