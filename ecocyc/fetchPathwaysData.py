#!/usr/bin/python

# requires
#   pip install beautifulsoup4
# NOTE: This script was not completely because we gained access to the ftp download for the equivalent flat files

import argparse
import httplib
import os.path
import re
import sys
import urllib
from bs4 import BeautifulSoup

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser('Download ecocyc pathways via their web service.')
parser.add_argument('dataPath', help='path to put the data.')
args = parser.parse_args()

dataPath = args.dataPath

# Sanity
if not os.path.isdir(dataPath):
  print >> sys.stderr, "No such directory [%s]" % dataPath
  sys.exit(1)

pathwayRe = re.compile("object=([^&]+)")

conn = httplib.HTTPConnection("biocyc.org")
conn.request("GET", "/ECOLI/class-instances?object=Pathways")
resp = conn.getresponse()
print resp.status, resp.reason

pathways = set()

soup = BeautifulSoup(resp.read(), 'html.parser')
conn.close()

for tag in soup.find_all(href=re.compile("type=PATHWAY")):
  uhref = urllib.unquote(tag['href'])
  m = pathwayRe.search(uhref)
  pathways.add(m.group(1))

pathways = sorted(pathways)

print "PATHWAYS:"

for p in pathways:
  print p

print "Got %d pathways" % (len(pathways))

# Retrieve first pathway as a test
conn = httplib.HTTPConnection("websvc.biocyc.org")
conn.request("GET", "/getxml?id=ECOLI:%s&detail=full" % pathways[0])
resp = conn.getresponse()
print resp.status, resp.reason
print "PATHWAY %s" % pathways[0]
pathwayRespXml = resp.read()
print pathwayRespXml
with open("%s/%s.xml" % (dataPath, pathways[0]), 'w') as f:
  f.write(pathwayRespXml)
# Retrieve genes for first pathway as a test
conn.request("GET", "/apixml?fn=genes-of-pathway&id=ECOLI:%s&detail=full" % pathways[0])
resp = conn.getresponse()
print resp.status, resp.reason
print "GENES for %s:" % pathways[0]
pathwayGenesRespXml = resp.read()
print pathwayGenesRespXml
with open("%s/%s-genes.xml" % (dataPath, pathways[0]), 'w') as f:
  f.write(pathwayGenesRespXml)

conn.close()
