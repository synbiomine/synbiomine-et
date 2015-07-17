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
currentSymLinkName = "current";
sections = [ "eggnog", "genbank", "go-annotation", "intermine", "kegg", "kegg-reaction", "taxons", "uniprot" ]
projectXmlPath = "intermine/project.xml"

############
### MAIN ###
############
parser = MyParser('Prepare a new dataset structure in the data repository.')
parser.add_argument('projectXmlTemplatePath', help='path to the project xml template')
parser.add_argument('repositoryPath', help='path to the repository.')
args = parser.parse_args()

repoPath = args.repositoryPath
templatePath = os.path.join('../..', args.projectXmlTemplatePath)

if not os.path.exists(repoPath):
  os.mkdir(repoPath)

os.chdir(repoPath)

# datasetDirName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
datasetDirName = datetime.datetime.now().strftime("%Y-%m-%d")

if os.path.exists(datasetDirName):
  raise Exception("Dataset path %s already exists!" % datasetDirName)

os.mkdir(datasetDirName)

if os.path.exists(currentSymLinkName):
  os.remove(currentSymLinkName)

os.symlink(datasetDirName, currentSymLinkName)

os.chdir(currentSymLinkName)

for section in sections:
  os.mkdir(section)

shutil.copy(templatePath, projectXmlPath)

print "Created dataset structure at %s" % (os.path.join(repoPath, datasetDirName))
