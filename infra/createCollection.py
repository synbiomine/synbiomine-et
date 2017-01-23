#!/usr/bin/env python3

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
parser = imu.ArgParser('Prepare a new dataset structure in the data repository')
parser.add_argument('projectXmlPath', help='path to the project XML template')
parser.add_argument('modelPath', help='path to the mine model XML')
parser.add_argument('datasetPath', help='path for the dataset')
args = parser.parse_args()

templatePath = args.projectXmlPath
modelPath = args.modelPath
datasetPath = args.datasetPath
newDatasetSymlinkPath = "%s/%s" % (datasetPath, newDatasetSymlink)

if os.path.exists(datasetPath):
    raise Exception("Dataset path %s already exists!" % datasetPath)

os.mkdir(datasetPath)
os.mkdir("%s/%s" % (datasetPath, logsDir))

for section in sections:
    sectionPath = "%s/%s" % (datasetPath, section)
    os.mkdir(sectionPath)

projectXmlPath = "%s/intermine/project.xml" % datasetPath
shutil.copy(templatePath, projectXmlPath)

datasetModelPath = "%s/intermine/genomic_model.xml" % datasetPath
shutil.copy(modelPath, datasetModelPath)

os.symlink(os.path.basename(datasetPath), newDatasetSymlinkPath)

print('Created dataset structure at %s, symlinked %s' % (datasetPath, newDatasetSymlink))