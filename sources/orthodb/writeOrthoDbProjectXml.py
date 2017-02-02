#!/usr/bin/env python

import jargparse
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.project as imp
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Add orthodb source entries to InterMine SynBioMine project XML.')
parser.add_argument('colPath', help='path to the dataset collection.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('orthodb')
ds.startLogging(__file__)

imp.addSourcesToProject(
    dc.getProjectXmlPath(),
    [
        imp.Source(
            'orthodb', 'orthodb',
            [
                { 'name':'src.data.dir',        'location':'data/orthodb/load' },
                { 'name':'orthodb.organisms',   'value':dc.getTaxonsAsString() }
            ],
            dump=True)
    ])
