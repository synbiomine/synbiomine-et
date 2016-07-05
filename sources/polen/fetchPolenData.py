#!/usr/bin/env python

import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.utils as imu
import synbio.data as sbd

############
### MAIN ###
############
parser = imu.ArgParser('Fetch POLEN data into the data collection')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')

partsUrl = 'http://synbio.ncl.ac.uk:8083/notification/messagesByTopic/Part/0/2147483647'
partsPath = '%s/part-messages.json' % (ds.getRawPath())

print 'Retrieving part messages from %s to %s' % (partsUrl, partsPath)

with open(partsPath, 'w') as f:
    # For convenience, we fetch all the parts at once.  2147483647 is the maximum polen will deal with before internal error
    r = requests.get(partsUrl)
    f.write(r.text)