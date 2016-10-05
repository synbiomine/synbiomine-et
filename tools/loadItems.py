#!/usr/bin/env python

import jargparse
import xmltodict

# THEORETICAL TODO IN ORDER TO UPDATE EXISTING ORGANISM NAMES WHERE A NAME DOES NOT ALREADY EXIST
# load organisms from polen items xml
# replace names in organism tables that match the taxonid
# re-trigger necessary post-processing (probably just search index rebuild)

############
### MAIN ###
############
parser = jargparse.ArgParser('Add organism names to table where no name currently exists')
parser.add_argument('path', help='path to the items file')
args = parser.parse_args()

with open(args.path) as f:
    items = xmltodict.parse(f, force_list=('attribute', 'collection', 'item', 'reference'))['items']['item']

print 'Got %d items from %s' % (len(items), args.path)

orgs = []

for item in items:
    if item['@class'] == 'Organism':
        orgs.append(item)

print 'Got %d organisms' % len(orgs)

for org in orgs:
    print '%d: %s' % (org['@taxonId'], org['@name'])