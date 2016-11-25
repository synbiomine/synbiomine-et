#!/usr/bin/env python

import jargparse
import json
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
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
Get the parts messages from POLEN
"""
def getPolenPartsMessages(ds):
    messagesPath = "%s/messages" % ds.getRawPath()

    if not os.path.exists(messagesPath):
        os.mkdir(messagesPath)

    partsUrl = 'http://synbio.ncl.ac.uk:8083/notification/messagesByTopic/Part/0/2147483647'
    partsPath = '%s/part-messages.json' % (messagesPath)

    # We're going to write the messages json to a file as well as return it so that we have a record
    print 'Retrieving part messages from %s to %s' % (partsUrl, partsPath)

    with open(partsPath, 'w') as f:
        # For convenience, we fetch all the parts at once.  2147483647 is the maximum polen will deal with before internal error
        r = requests.get(partsUrl)
        f.write(r.text)

    return json.loads(r.text)

"""
Given a dataset, retrieve the POLEN parts.
"""
def getPolenPartsMd(polenMessagesJson):
    partsMd = {}

    for message in polenMessagesJson['messages']:
        content = message['content']

        # We assume that the part name is the fixed ID.  The last message contains the most uptodate data
        partsMd[content['name']] = PolenPartMetadata(content['name'], content['description'], content['uri'])

    return partsMd

"""
Given POLEN parts metadata, get the actual data files for a given component (currently 'parts' or 'interactions')
"""
def getVPRepoComponents(ds, polenPartsMd, componentName, componentUriSuffix):
    myComponentsPath = '%s/%s' % (ds.getRawPath(), componentName)

    if not os.path.exists(myComponentsPath):
        os.mkdir(myComponentsPath)

    gotCount = 0

    for partMd in polenPartsMd.values():
        # At the moment, all parts come from virtualparts.org and the only uri we are given is for the sbol
        # But for InterMine, we want the actual part XML page which is given by replacing 'sbol' on the end of the uri
        # with 'xml'
        uri = '%s/%s' % (os.path.dirname(partMd.uri), componentUriSuffix)
        uriComponents = uri.split('/')
        myComponentSuffixIndex = -1
        myComponentSuffix = uriComponents[myComponentSuffixIndex]
        myComponentName = uriComponents[myComponentSuffixIndex - 1 - componentUriSuffix.count('/')]
        myComponentPath = "%s/%s.%s" % (myComponentsPath, myComponentName, myComponentSuffix)

        print "Fetching %s => %s" % (uri, myComponentPath)
        r = requests.get(uri)
        if r.status_code == 500:
            print "*** Ignoring %s due to server status code %d" % (uri, r.status_code)
            continue

        gotCount += 1

        with open(myComponentPath, 'w') as f:
            f.write(r.text)

    print "Got %d %s from %d metadata" % (gotCount, componentName, len(polenPartsMd))

############
### MAIN ###
############
parser = jargparse.ArgParser('Fetch POLEN data into the data collection')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

polenMessagesJson = getPolenPartsMessages(ds)
polenPartsMetadata = getPolenPartsMd(polenMessagesJson)
getVPRepoComponents(ds, polenPartsMetadata, 'parts', 'xml')
getVPRepoComponents(ds, polenPartsMetadata, 'interactions', 'interactions/xml')
