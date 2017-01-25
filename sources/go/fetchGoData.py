#!/usr/bin/env python3

import jargparse
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Fetch Gene Ontology files')
parser.add_argument('datasetPath', help='path to the dataset location')
args = parser.parse_args()

dc = sbd.Collection(args.datasetPath)
ds = dc.getSet('go')
ds.startLogging(__file__)

uri = 'http://geneontology.org/ontology/go-basic.obo'
destPath = ds.getLoadPath() + uri.split('/')[-1]

print('Fetching %s => %s' % (uri, destPath))
r = requests.get(uri)

with open(destPath, 'w') as f:
    f.write(r.text)
