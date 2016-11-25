#!/usr/bin/env python3

import jargparse
import json
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import synbio.data as sbd

#################
### CONSTANTS ###
#################
partsSummaryFilename = 'partsSummary.json'

############
### MAIN ###
############
parser = jargparse.ArgParser('Fetch Synbis parts')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

partsSummaryPath = ds.getRawPath()

r = requests.get('http://synbis.bg.ic.ac.uk/synbisapi/searchlist/datasheet')
with open(partsSummaryPath + partsSummaryFilename, 'w') as f:
    f.write(r.text)

partsSummary = json.loads(r.text)

partIds = []

for partSummary in partsSummary:
    partIds.append(partSummary['displayID'])

print('Found %d part IDs' % len(partIds))

partsPath = ds.getRawPath() + 'parts/'
os.mkdir(partsPath)

for partId in partIds:
    partUrl = 'http://synbis.bg.ic.ac.uk/synbisapi/datasheet/' + partId
    print('Fetching %s' % partUrl)

    r = requests.get(partUrl)
    with open(partsPath + partId + '.xml', 'w') as f:
        f.write(r.text)