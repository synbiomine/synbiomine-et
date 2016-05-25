#!/usr/bin/env python

import argparse
import os
import sys
import shutil

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp

class Logger(object):
    def __init__(self, logPath):
        self.terminal = sys.stdout
        self.log = open(logPath, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser('Add OrthoDB project entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('orthoDbDataPath', help='path to the OrthoDB data')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
orthoDbDataPath = args.orthoDbDataPath

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath
taxonsPath = "%s/taxons/taxons.txt" % datasetPath

with open(taxonsPath) as f:
    taxons = f.read()

project = imp.Project("%s/intermine/project.xml" % datasetPath)
source = imp.Source(
    'orthodb', 'orthodb',
    [
        { 'name':'src.data.dir', 'location':orthoDbDataPath },
        { 'name':'orthodb.organisms', 'value':taxons }
    ],
    dump=True)

project.addSource(source)
print project.toString()

shutil.copy(projectXmlPath, "%s.bak" % projectXmlPath)
project.write(projectXmlPath)