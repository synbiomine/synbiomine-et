#!/usr/bin/python

import argparse
import datetime
import os
import os.path

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

#################
### CONSTANTS ###
#################
currentSymLinkName = "current";

############
### MAIN ###
############
parser = MyParser('Prepare data repository structure.')
parser.add_argument('repositoryPath', help='path to the repository.')
args = parser.parse_args()

repoPath = args.repositoryPath

if not os.path.exists(repoPath):
  os.mkdir(repoPath)

os.chdir(repoPath)

datasetDirName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

if os.path.exists(datasetDirName):
  raise Exception("Dataset path %s already exists!" % datasetDirName)

os.mkdir(datasetDirName)

if os.path.exists(currentSymLinkName):
  os.remove(currentSymLinkName)

os.symlink(datasetDirName, currentSymLinkName)

print "Created dataset structure %s" % (os.path.join(repoPath, datasetDirName))
