#!/usr/bin/env python

# This is just a test script to check the parsing of GO data that we need (resolution of synonyms, chiefly).
# The actual parsing of GO terms is done by InterMine Java.

import jargparse
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import jbio.sources.go as go
import synbio.data as sbd

parser = jargparse.ArgParser('Test parse the Gene Ontology')
parser.add_argument('datasetPath', help='path to the dataset location')
args = parser.parse_args()

dc = sbd.Collection(args.datasetPath)
ds = dc.getSet('go')

goPath = "%s/%s" % (ds.getLoadPath(), 'go-basic.obo')
go.getSynonoyms(goPath)