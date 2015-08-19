#!/usr/bin/python

# requires
#   pip install beautifulsoup4

import httplib
import re
import urllib
from bs4 import BeautifulSoup

############
### MAIN ###
############
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
print resp.read()

# Retrieve genes for first pathway as a test
conn.request("GET", "/apixml?fn=genes-of-pathway&id=ECOLI:%s&detail=full" % pathways[0])
resp = conn.getresponse()
print resp.status, resp.reason
print "GENES for %s:" % pathways[0]
print resp.read()

conn.close()
