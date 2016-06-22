#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.project as imp
import intermyne.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add promoter source entries to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath

logPath = "%s/logs/writePromotersProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
            'dbtbs-regulation-Bsub168', 'synbio-regulation',
            [
                { 'name':'src.data.dir',        'location':'data/current/promoters/dbtbs' },
            ]),
        imp.Source(
            'nicolas2012-regulation-Bsub168', 'synbio-regulation',
            [
                { 'name':'src.data.dir',        'location':'data/current/promoters/nicolas-2012' },
            ])
    ])