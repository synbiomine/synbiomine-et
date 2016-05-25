#!/usr/bin/env python

import os
import sys
import shutil

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add OrthoDB source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('orthoDbDataPath', help='path to the OrthoDB data')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
orthoDbDataPath = args.orthoDbDataPath

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath
taxonsPath = "%s/taxons/taxons.txt" % datasetPath

with open(taxonsPath) as f:
    taxons = f.read().strip()

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