#!/usr/bin/python

# requires
#   pip install beautifulsoup4 html5lib
# 
# This script exists to scrape out lists of IGEM parts from their web pages
# At the moment, only doing transcription regulators as a test
# http://parts.igem.org/Protein_coding_sequences/Transcriptional_regulators
#
# We need to do it this way because there's no API way to get a list of parts atm
# And the data dumps they provide are too old (newest from 2010)
#
# Of course, this is a horribly fragile way to do it, so an IGEM API to do this would be vastly better

import argparse
import httplib
import json
import sys
import texttable
from bs4 import BeautifulSoup

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

class Part(object):
  def __init__(self):
    self.name = 'UNSET'
    self.description = ''
    self.proteinName = ''
    self.uniprotName = ''

#################
### FUNCTIONS ###
#################
def writePretty(parts, outFile):
  summaryTable = texttable.Texttable()
  summaryTable.set_cols_width([16, 16, 16, 64])
  summaryTable.add_row(['Part', 'Protein', 'Uniprot', 'Description'])

  for part in parts:
    # We need to strip out uniccode for texttable - might need to loko for another module
    summaryTable.add_row([part.name.encode('ascii', 'ignore'), part.proteinName.encode('ascii', 'ignore'), part.uniprotName.encode('ascii', 'ignore'), part.description.encode('ascii', 'ignore')])

  print summaryTable.draw()

def writeJson(parts, outFile):
  jsonParts = []

  for part in parts:
    jsonPart = { 'description' : part.description, 'proteinName' : part.proteinName, 'uniprotName' : part.uniprotName }
    jsonParts.append({ part.name : jsonPart})

  print >> outFile, json.dumps(jsonParts, indent=4)

# Scrape part information out of an IGEM summary page
def scrapeParts(host, url):
  conn = httplib.HTTPConnection(host)

  print "Fetching http://%s%s" % (host, url)
  conn.request("GET", url)
  resp = conn.getresponse()

  # We have to use html5lib here because the iGEM pages are malformed (e.g. all <tr>s inside the last <th> tag because it wasn't closed - something a browser corrects automatically
  soup = BeautifulSoup(resp.read(), 'html5lib')
  conn.close()

  # Multiple tables with this id on a page
  tables = soup.find_all('table', id='assembly_plasmid_table')
  parts = []

  for table in tables:
    # print '### TABLE ###'

    for row in table.tbody.find_all('tr')[1:-1]:
      cols = row.find_all('td')

      if args.verbose:
        print 'Processing row',

      part = Part()
      part.name = cols[0].a.contents[0].strip()

      if args.verbose:
        print part.name

      part.proteinName = cols[1].contents[0].strip()
      part.description = cols[2].contents[0].strip()
      part.uniprotName = cols[5].contents[0].strip()

      parts.append(part)

  return parts

############
### MAIN ###
############
host = "parts.igem.org"
url = "/Protein_coding_sequences/Transcriptional_regulators"

parser = MyParser('Scrape iGEM part metadata.')
parser.add_argument('outFile', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Parts output file.  If not given then output is printed to STDOUT')
parser.add_argument('-p', '--pretty', action='store_true', help="If set, output part information in table format, otherwise output is JSON")
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

parts = scrapeParts(host, url)

if args.pretty:
  writePretty(parts, args.outFile)
else:
  writeJson(parts, args.outFile)
