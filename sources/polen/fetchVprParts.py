#!/usr/bin/env python

import jargparse
import xml.etree.ElementTree as ET
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Fetch Virtual Parts Repository parts directly')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

# Uses api from http://virtualparts.org/repositorydocumentation
pageNum = 1

while True:
    url = 'http://virtualparts.org/parts/page/%d/xml' % pageNum
    print "Fetching page %s" % url
    r = requests.get(url)

    # We're doing this processing so that we get individual parts files that we can compare with what we get when
    # we do individual parts requests from POLEN
    tree = ET.fromstring(r.text)

    part_es = tree.findall('./Part')
    print 'Found %d parts in page %d' % (len(part_es), pageNum)

    if len(part_es) <= 0:
        break
    else:
        pageNum += 1

# TODO: output each part in its own xml file