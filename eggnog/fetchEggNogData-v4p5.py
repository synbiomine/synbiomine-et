#!/usr/bin/python

import argparse
import os
import sys
import wget

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.utils as imu

#################
### FUNCTIONS ###
#################
def logEyeCatcher(text):
    print "~~~ %s ~~~" % text

def assemblePrereqFiles(localDir, remoteUrlStub, paths):
    logEyeCatcher("Downloading files")

    for path in paths:
        remoteUrl = "%s/%s" % (remoteUrlStub, path)
        dir = "%s/%s" % (localDir, os.path.dirname(path))

        if beVerbose:
            print "Downloading %s to %s" % (remoteUrl, dir)

        if not os.path.exists(dir):
            os.makedirs(dir)

        wget.download(remoteUrl, out = dir)

############
### MAIN ###
############
parser = imu.ArgParser('Retrieve required EggNOG files.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

beVerbose = args.verbose
datasetPath = args.datasetPath
eggNogPath = "%s/eggnog" % datasetPath
logPath = "%s/logs/fetchEggnogData.log" % datasetPath
sys.stdout = imu.Logger(logPath)

eggNogUrlStub = "http://eggnogdb.embl.de/download/eggnog_4.5/"
files = set(['eggnog4.functional_categories.txt', 'data/bactNOG/bactNOG.annotations.tsv.gz', 'data/bactNOG/bactNOG.members.tsv.gz'])

assemblePrereqFiles(eggNogPath, eggNogUrlStub, files)