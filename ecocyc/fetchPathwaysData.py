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
# pathwayRe = re.compile("object=(
conn = httplib.HTTPConnection("biocyc.org")
conn.request("GET", "/ECOLI/class-instances?object=Pathways")
resp = conn.getresponse()
print resp.status, resp.reason
# print "[%s]" % resp.read()

soup = BeautifulSoup(resp.read(), 'html.parser')

for tag in soup.find_all(href=re.compile("type=PATHWAY")):
  print tag
  # tag['href']

conn.close()
