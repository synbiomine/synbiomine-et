#!/usr/bin/env python3

import jargparse
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Generate organism entries for $INTERMINE/synbiomine/webapp/resources/webapp/dataCategories.jsp')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
orgs = dc.getOrganisms()

for taxonId, name in sorted(orgs.items(), key=lambda item: item[1]):
    print('  <li>%s (<i>taxon %d</i>)</li>' % (orgs[taxonId], taxonId))