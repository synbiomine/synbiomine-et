#!/usr/bin/python

import datetime
import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.utils as imu

#################
### CONSTANTS ###
#################
sections = [ "eggnog", "genbank", "goa", "intermine", "kegg", "taxons", "uniprot" ]
logsDir = "logs"

############
### MAIN ###
############
parser = imu.ArgParser('Prepare a new dataset structure in the data repository')
parser.add_argument('projectXmlPath', help='path to the project XML template')
parser.add_argument('modelPath', help='path to the mine model XML')
parser.add_argument('repositoryPath', help='path to the data repository')
args = parser.parse_args()

repoPath = args.repositoryPath
templatePath = args.projectXmlPath
modelPath = args.modelPath

if not os.path.exists(repoPath):
    os.mkdir(repoPath)

# datasetDirName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
datasetDirName = datetime.datetime.now().strftime("%Y-%m-%d")
datasetPath = "%s/%s" % (repoPath, datasetDirName)

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

print "Created dataset structure at %s" % (os.path.join(repoPath, datasetDirName))