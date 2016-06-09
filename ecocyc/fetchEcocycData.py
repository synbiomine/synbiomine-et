#!/usr/bin/env python

import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Copy necessary downloaded ecocyc files into the dataset')
parser.add_argument('dataPath', help='path for downloaded Ecocyc pathways.col and pathways.dat files')
parser.add_argument('datasetPath', help='path to the dataset location')
args = parser.parse_args()

dataPath = args.dataPath
datasetPath = args.datasetPath
ecoCycDatasetPath = "%s/ecocyc" % (datasetPath)

os.mkdir(ecoCycDatasetPath)

for file in ['data/pathways.col', 'data/pathways.dat']:
    fromPath = "%s/%s" % (dataPath, file)
    toPath = ecoCycDatasetPath

    print "Copying %s to %s" % (fromPath, toPath)
    shutil.copy(fromPath, toPath)