#!/usr/bin/env python

import json
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.utils as imu
import synbio.data as sbd

###############
### CLASSES ###
###############
class PolenPartMetadata:
    def __init__(self, name, description, uri):
        self.name = name
        self.description = description
        self.uri = uri

#################
### FUNCTIONS ###
#################
"""
Given a dataset, retrieve the POLEN parts.
"""
def getPolenPartsMd(ds):
    partsMd = {}

    messagesPath = "%s/part-messages.json" % (ds.getRawPath())
    with open(messagesPath) as f:
        data = json.load(f)

    for message in data['messages']:
        content = message['content']

        # We assume that the part name is the fixed ID.  The last message contains the most uptodate data
        partsMd[content['name']] = PolenPartMetadata(content['name'], content['description'], content['uri'])

    return partsMd


"""
Given POLEN parts metadata, get the actual data files that we're interested in.
"""
def getParts(ds, polenPartsMd):
    gotCount = 0

    for partMd in polenPartsMd.values():
        # At the moment, all parts come from virtualparts.org and the only uri we are given is for the sbol
        # But for InterMine, we want the actual part XML page which is given by replacing 'sbol' on the end of the uri
        # with 'xml'
        uri = "%s/xml" % os.path.dirname(partMd.uri)
        uriComponents = uri.split('/')
        ourPartPath = "%s/%s.%s" % (ds.getRawPath(), uriComponents[-2], uriComponents[-1])

        with open(ourPartPath, 'w') as f:
            print "Fetching %s => %s" % (uri, ourPartPath)
            r = requests.get(uri)
            if r.status_code == 500:
                print "*** Ignoring %s due to server status code %d" % (uri, r.status_code)
                continue

            gotCount += 1
            f.write(r.text)

    print "Got %d parts from %d metadata" % (gotCount, len(polenPartsMd))

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

polenPartsMetadata = getPolenPartsMd(ds)
getParts(ds, polenPartsMetadata)
