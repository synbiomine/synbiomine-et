#!/usr/bin/python

import argparse
import os
import os.path
import sys
import wget

class Logger(object):
    def __init__(self, logPath):
        self.terminal = sys.stdout
        self.log = open(logPath, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def fileno(self):
        return self.log.fileno()

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

#################
### FUNCTIONS ###
#################
def logEyeCatcher(text):
    print "~~~ %s ~~~" % text

def assemblePrereqFiles(localDir, remoteUrlStub, paths):
    logEyeCatcher("Downloading files")

    for path in paths:
        dir = "%s/%s" % (localDir, os.path.dirname(path))

        if not os.path.exists(dir):
            os.makedirs(dir)

        wget.download("%s/%s" % (remoteUrlStub, path), out = dir)

############
### MAIN ###
############
parser = MyParser('Retrieve required EggNOG files.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
eggNogPath = "%s/eggnog" % datasetPath
logPath = "%s/logs/fetchEggnogData.log" % datasetPath
sys.stdout = Logger(logPath)

eggNogUrlStub = "http://eggnogdb.embl.de/download/"
files = set(['eggnogv4.funccats.txt', 'data/bactNOG/bactNOG.annotations.gz', 'data/bactNOG/bactNOG.members.tsv.gz'])

assemblePrereqFiles(eggNogPath, eggNogUrlStub, files)