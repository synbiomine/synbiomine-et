#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add EggNOG source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath

logPath = "%s/logs/writeEggNogProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
            'eggnog-functional-categories', 'synbio-funccat',
            [
                { 'name':'src.data.dir',        'location':'data/eggnog' }
            ],
            dump=False)
    ])