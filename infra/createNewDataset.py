#!/usr/bin/python

import argparse
import datetime
import os
import os.path
import shutil
import sys

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

#################
### CONSTANTS ###
#################
sections = [ "eggnog", "genbank", "go-annotation", "intermine", "kegg", "kegg-reaction", "taxons", "uniprot" ]
logsDir = "logs"

############
### MAIN ###
############
parser = MyParser('Prepare a new dataset structure in the data repository.')
parser.add_argument('projectXmlTemplatePath', help='path to the project xml template')
parser.add_argument('repositoryPath', help='path to the data repository.')
args = parser.parse_args()

repoPath = args.repositoryPath
templatePath = args.projectXmlTemplatePath

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

print "Created dataset structure at %s" % (os.path.join(repoPath, datasetDirName))
