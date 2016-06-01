#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add GEO source entries to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath

logPath = "%s/logs/writeGeoProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
            'faith-GEOSeries-EcoliK12', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/geo/faith-2007' },
            ]),
        imp.Source(
            'nicolas2012-GEOSeries-Bsub168', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/geo/nicolas-2012' },
            ])
    ])