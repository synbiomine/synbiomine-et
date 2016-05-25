#!/usr/bin/python

# Filters the output from fetchIgemMetadata.py to return only parts that we can tell are derived from E. coli
# This currently misses a lot, as we only identify a part if it has a UniProt protein entry and that entry is for E. coli K-12

import httplib
import json
import os
import sys
import StringIO
from lxml import etree

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.utils as imu

###############
### CLASSES ###
###############
class Part(object):
  def __init__(self):
    self.name = 'UNSET'
    self.description = ''
    self.proteinName = ''
    self.uniprotName = ''

#################
### FUNCTIONS ###
#################
def readPartsFromJson(inFile):
  partsJson = json.load(inFile)
  # print json.dumps(partsJson, indent=4)
  parts = {}

  for name, partJson in partsJson.iteritems():
    part = Part()
    part.name = name
    part.description = partJson['description']
    part.proteinName = partJson['proteinName']
    part.uniprotName = partJson['uniprotName']

    parts[name] = part

  return parts

def writeJson(parts, outFile):
  jsonParts = {}

  for part in parts:
    jsonPart = { 'description' : part.description, 'proteinName' : part.proteinName, 'uniprotName' : part.uniprotName }
    jsonParts[part.name] = jsonPart

  print >> outFile, json.dumps(jsonParts, indent=4)

############
### MAIN ###
############
parser = imu.ArgParser('Filter scraped iGEM part metadata for parts which obviously derive from E. coli K-12')
parser.add_argument('inFile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Parts input file.  If not given then input is STDIN')
parser.add_argument('outFile', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Filtered parts output file.  If not given then output is STDOUT')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

uniprotHost = 'www.uniprot.org'
uniprotUrlStub = '/uniprot/'
# E.coli K-12
taxonIdToFind = 83333

if args.verbose:
  print "Looking for parts with taxon %s" % taxonIdToFind

parts = readPartsFromJson(args.inFile)
filteredParts = {}

for name, part in parts.iteritems():
  if part.uniprotName != '':
    if args.verbose:
      print "Checking part %s, protein %s, uniprot %s" % (part.name, part.proteinName, part.uniprotName)

    url = uniprotUrlStub + '%s.xml' % part.uniprotName
    conn = httplib.HTTPConnection(uniprotHost)
    conn.request('GET', url)
    resp = conn.getresponse()

    if resp.status != 200:
      print >> sys.stderr, "ERROR: Response from http://%s%s was %s.  Ignoring" % (uniprotHost, url, resp.status)
    else:
      # uniprotXml = etree.fromstring(resp.read())
      parser = etree.XMLParser(remove_blank_text=True)
      uniprotXml = etree.parse(StringIO.StringIO(resp.read()), parser)
      taxonId = int(uniprotXml.xpath('/n:uniprot/n:entry/n:organism/n:dbReference/@id', namespaces={'n':'http://uniprot.org/uniprot'})[0])
      # print etree.tostring(uniprotXml, pretty_print=True)
      # taxonId = uniprotXml.findall('/uniprot')
      if taxonId == taxonIdToFind:
        filteredParts[part.name] = part
      elif args.verbose:
        print "Ignoring part since taxon of %s is not %s" % (taxonId, taxonIdToFind)
  else:
    if args.verbose:
      print "Ignoring %s since it has no protein listed" % part.name

writeJson(filteredParts.values(), args.outFile)

if args.verbose:
  print "Found %d parts" % len(filteredParts)
