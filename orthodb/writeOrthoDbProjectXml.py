#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.project as imp
import intermyne.utils as imu
import synbio.dataset as sbds

############
### MAIN ###
############
parser = imu.ArgParser('Add OrthoDB source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('orthoDbDataPath', help='path to the OrthoDB data')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
ds = sbds.Dataset(datasetPath)
orthoDbDataPath = args.orthoDbDataPath

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
            'orthodb', 'orthodb',
            [
                { 'name':'src.data.dir',        'location':orthoDbDataPath },
                { 'name':'orthodb.organisms',   'value':ds.getTaxonsAsString() }
            ],
            dump=True)
    ])