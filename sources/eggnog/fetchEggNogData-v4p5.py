#!/usr/bin/python

import os
import sys
import wget

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.utils as imu
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def assemblePrereqFiles(localDir, remoteUrlStub, paths):
    imu.printSection('Downloading files')

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
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

beVerbose = args.verbose

dc = sbd.Collection(args.colPath)
ds = dc.getSet('eggnog')
ds.startLogging(__file__)

eggNogUrlStub = "http://eggnogdb.embl.de/download/eggnog_4.5/"
files = {'eggnog4.functional_categories.txt', 'data/bactNOG/bactNOG.annotations.tsv.gz', 'data/bactNOG/bactNOG.members.tsv.gz'}

assemblePrereqFiles(ds.getLoadPath(), eggNogUrlStub, files)
