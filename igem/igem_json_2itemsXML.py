#!/usr/bin/python

import argparse
import json
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.model as IM

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

############
### MAIN ###
############
parser = MyParser('Tranform IGEM JSON files in out format after scraping to InterMine item import XML.')
parser.add_argument('imModelFile', help='the file containing the InterMine data model.')
parser.add_argument('inFile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Parts input file.  If not given then input is STDIN')
parser.add_argument('outFile', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='InterMine items XML file.  If not given then output is STDOUT')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

model = IM.Model(args.imModelFile)
doc = IM.Document(model)

dataSourceItem = doc.createItem("DataSource")
dataSourceItem.addAttribute('name', 'IGEM Registry of Standard Biological Parts')
dataSourceItem.addAttribute('url', 'http://parts.igem.org')
doc.addItem(dataSourceItem)

dataSetItem = doc.createItem("DataSet")
dataSetItem.addAttribute('name', 'IGEM Parts')
dataSetItem.addAttribute('dataSource', dataSourceItem)
doc.addItem(dataSetItem)

parts = readPartsFromJson(args.inFile)

if args.verbose:
  print "Read %d parts" % len(parts)

proteinItems = {}

for part in parts.values():
  if args.verbose:
    print "Processing part %s" % part.name

  if part.uniprotName not in proteinItems:
    proteinItem = doc.createItem("Protein")
    proteinItem.addAttribute("primaryAccession", part.uniprotName)
    proteinItems[part.uniprotName] = proteinItem

  proteinItem = proteinItems[part.uniprotName]

  partItem = doc.createItem("IGEMPart")
  partItem.addAttribute("identifier", part.name)
  partItem.addAttribute("description", part.description)
  partItem.addAttribute("protein", proteinItem)
  partItem.addToAttribute("dataSets", dataSetItem)

  proteinItem.addToAttribute("igemParts", partItem)

  doc.addItem(partItem)

for proteinItems in proteinItems.values():
  doc.addItem(proteinItem)

doc.write(args.outFile)
