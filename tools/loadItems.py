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
    d = xmltodict.parse(f, force_list=('attribute', 'collection', 'item', 'reference'))

print 'Got %d items from %s' % (len(d['items']['item']), args.path)
