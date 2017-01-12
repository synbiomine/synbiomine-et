#!/usr/bin/env python3

import glob
import jargparse
import os
#import re
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import intermyne.metadata as immd
import intermyne.model as imm
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Do a little bit of preprocessing correction on synbis files that hopefully won''t be necessary in the future.')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-d', '--dummy', action='store_true', help='dummy run, do not store anything')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

# replaceRe = re.compile('.* xmlns:synbis="http://synbis.bg.ic.ac.uk" .*')

partsGlob = ds.getRawPath() + 'parts/*.xml'
print('Processing ' + partsGlob)

for path in glob.glob(partsGlob):
    print('Processing ' + path)

    with open(path) as f:
        text = f.read()
        text = text.replace(' xmlns:synbis="http://synbis.bg.ic.ac.uk" ', ' xmlns:synbis="http://synbis.bg.ic.ac.uk/" ')

    os.unlink(path)
    with open(path, 'w') as f:
        f.write(text)
