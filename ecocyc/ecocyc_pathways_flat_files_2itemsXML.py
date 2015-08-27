#!/usr/bin/python

import argparse
from lxml import etree as ET
import os
import os.path
import sys
import urllib

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

###################
### SUBROUTINES ###
###################
"""
Process the file linking pathways to genes

Returns a data structure with the format:
{ 
  'UNIQUE-ID' : 
    'UNIQUE-ID' : [ <id> ]
    'NAME' : [ <name> ]
    'GENE-NAME' : [ <gene-name>* ]
    'GENE-ID' : [ <gene-id>* ]
}
"""
def processPathwaysColFile(fn):
  pathways = {}

  # We need to ignore the first line which is column headers
  seenHeaders = False

  with open(fn) as f:
    for line in f:
      line = line.strip(os.linesep)

      # Ignore comments
      if line.startswith('#'):
        continue

      values = line.split('\t')

      if not seenHeaders:
        seenHeaders = True
        headers = values
        continue

      pathway = {}

      for i, value in enumerate(values):
        name = headers[i]
        # print "Got %s:%s" % (name, value)

        # Setup new pathway record
        if name == 'UNIQUE-ID':
          # print "Processing genes for pathway %s" % value
          pathways[value] = pathway

        # Add value to key entry
        if not name in pathway:
          pathway[name] = []

        pathway[name].append(value)

  return pathways

"""
Process the pathways information file

Returns a data structure with the format:
{ 
  'UNIQUE-ID' : 
    'UNIQUE-ID' : [ <id> ]
    'COMMON-NAME' : [ <name> ]
    'COMMENT' : [ <gene-name>* ]
    * : [ * ]
}
"""
def processPathwaysDatFile(fn):
  pathways = {}

  with open("%s/%s" % (inputDn, pathwaysDatFn)) as f:
    # Used to add continued lines
    lastKey = None

    pathway = None

    for line in f:
      line = line.strip(os.linesep)
      line = urllib.unquote(line)

      # Ignore comments
      if line.startswith('#'):
        continue

      # Terminate record
      if line == '//':
        if pathway == None:
          print >> sys.stderr, "Found record end with no associated pathway."
          sys.exit(1)
        else:
          # print "Ending record for pathway %s" % pathway['UNIQUE-ID'][0]

          pathways[pathway['UNIQUE-ID'][0]] = pathway
          pathway = None
          lastKey = None
          continue

      # Process continued line
      if line.startswith('/'):
        if pathway == None:
          print >> sys.stderr, "Found continued line but with no current pathway."
          sys.exit(1)
        if lastKey == None:
          print >> sys.stderr, "Found continued line for pathway %s but with no last key." % pathway['UNIQUE-ID']
          sys.exit(1)
        else:
          line = " " + line[1:]
          pathway[lastKey][-1] += line
          continue

      # Complain if we now have a line not containing '-'
      # All such valid lines would be dealt with by the logic above
      if not '-' in line:
        print >> sys.stderr, "Did not find '-' in line [%s]" % line
        sys.exit(1)

      (key, value) = line.split(' - ', 1)
      # print "%s:%s" % (key, value)

      # Setup new pathway record
      if key == 'UNIQUE-ID':
        # Sanity
        if pathway != None:
          print >> sys.stderr, "Found new UNIQUE-ID %s but still have unfinished pathway %s" % (value, pathway['UNIQUE-ID'])
          sys.exit(1)

        # print "Processing pathway %s" % value

        pathway = {}

      # Add value to key entry
      if not key in pathway:
        pathway[key] = []

      pathway[key].append(value)

      lastKey = key

  if pathway != None:
    print >> sys.stderr, "Finished processing %s but still in unclosed pathway %s" % (pathwaysDatFn, pathway['UNIQUE-ID'])
    sys.exit(1)

  return pathways

############
### MAIN ###
############
parser = MyParser('Tranform ecocyc pathways flat files to InterMine items import XML.')
parser.add_argument('imModelFilename', help='the file containing the InterMine data model.')
parser.add_argument('inputDirname', help='the directory containing the input flat files.')
parser.add_argument('outputFilename', help='the output location for the generated items XML.')
args = parser.parse_args()

# This contains pathway details
pathwaysDatFn = "pathways.dat"

# This links gene ids to pathways
pathwaysColFn = "pathways.col"

if not os.path.isdir(args.inputDirname):
  print >> sys.stderr, "[%s] is not a directory" % args.inputDirname
  sys.exit(1)

model = IM.Model(args.imModelFilename)
doc = IM.Document(model)

inputDn = args.inputDirname
outputFn = args.outputFilename

pathways = processPathwaysDatFile("%s/%s" % (inputDn, pathwaysDatFn))
pathwaysToGenes = processPathwaysColFile("%s/%s" % (inputDn, pathwaysColFn))

print "Processed %d pathways" % len(pathways)

genesWritten = set()

# Yeah, we should write the python equivalent for the perl api here but for now let's be lazy
itemsTag = ET.Element("items")

for pathway in pathways.itervalues():
  # print "Writing pathway %s" % (pathway['UNIQUE-ID'][0])
  pathwayItem = doc.createItem("Pathway")
  pathwayItem.addAttribute('identifier', pathway['UNIQUE-ID'][0])
  pathwayItem.addAttribute('name', pathway['COMMON-NAME'][0])

  if 'COMMENT' in pathway:
    comment = pathway['COMMENT'][0]
  else:
    comment = ''

  pathwayItem.addAttribute('description', comment)

  doc.addItem(pathwayItem)

for pathway in pathwaysToGenes.itervalues():
  # print "Writing %d genes for pathway %s" % (len(pathway['GENE-NAME']), pathway['UNIQUE-ID'][0])

  for symbol in pathway['GENE-NAME']:
    if symbol == '':
      continue

    if not symbol in genesWritten:
      # print "Processing symbol %s" % symbol
      geneItem = doc.createItem("Gene")
      geneItem.addAttribute('symbol', symbol)
      doc.addItem(geneItem)
      genesWritten.add(symbol)

doc.write(outputFn)

print "Wrote %d genes in %d pathways" % (len(genesWritten), len(pathways))
