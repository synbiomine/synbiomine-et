#!/usr/bin/env python

# This is just a test script to check the parsing of GO data that we need (resolution of synonyms, chiefly).
# The actual parsing of GO terms is done by InterMine Java.

import jargparse
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import synbio.data as sbd

parser = jargparse.ArgParser('Test parse the Gene Ontology')
parser.add_argument('datasetPath', help='path to the dataset location')
args = parser.parse_args()

dc = sbd.Collection(args.datasetPath)
ds = dc.getSet('go')

goPath = "%s/%s" % (ds.getLoadPath(), 'go-basic.obo')
ids = set()

with open(goPath) as f:
    for line in f:
        line = line.strip()

        if line.find(':') > -1:
            (key, value) = line.split(':', 1)
            if key == 'id':
                ids.add(value)

for id in ids:
    print id

print "Got %d ids" % len(ids)