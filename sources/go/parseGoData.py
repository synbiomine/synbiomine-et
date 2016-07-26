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
fcIds = set()
synIds = {}
currentFcId = None

with open(goPath) as f:
    for line in f:
        line = line.strip()

        if line.find(':') > -1:
            (key, value) = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if key == 'id':
                currentFcId = value
                fcIds.add(currentFcId)
            elif key == 'alt_id':
                if value in synIds:
                    print "ERROR: Already found synonym %s => %s when trying to set up %s => %s" % (value, synIds[value], value, currentFcId)
                    sys.exit(2)
                else:
                    synIds[value] = currentFcId

for id in fcIds:
    print id

print "Got %d first class ids" % len(fcIds)
print "Got %d synonyms" % len(synIds)

synAndFcCount = 0
for synId in synIds.keys():
    if synId in fcIds:
        synAndFcCount += 1

print "Got %d synonyms that were also first-class IDs" % (synAndFcCount)
# print synIds['GO:0006350']