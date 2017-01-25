#!/usr/bin/env python3

import jargparse
import os
import shutil
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import synbio.data as sbd

#################
### CONSTANTS ###
#################
sections = [ 'eggnog', 'genbank', 'goa', 'kegg', 'taxons', 'uniprot' ]
logsDir = 'logs'
newDatasetSymlink = '../new'

############
### MAIN ###
############
parser = jargparse.ArgParser('Prepare a new data collection in the data repository')
parser.add_argument('colPath', help='path to where the new data collection should be')
args = parser.parse_args()

colPath = args.colPath
newDatasetSymlinkPath = "%s/%s" % (colPath, newDatasetSymlink)

if os.path.exists(colPath):
    raise Exception("Dataset path %s already exists!" % colPath)

os.mkdir(colPath)
os.mkdir('%s/%s' % (colPath, logsDir))
os.mkdir('%s/%s' % (colPath, 'intermine'))

shutil.copy('config/genomic_model.xml', '%s/intermine/genomic_model.xml' % colPath)

dc = sbd.Collection(colPath)

# Create the standard dataset structure in these paths
for section in sections:
    ds = dc.getSet(section)

os.symlink(os.path.basename(colPath), newDatasetSymlinkPath)

print('Created dataset structure at %s, symlinked %s' % (colPath, newDatasetSymlink))