#!/usr/bin/python

import argparse
from lxml import etree as ET
import os
import os.path
import sys
import urllib

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
Add an InterMine attribute from a pathway to the item XML tag
"""
def addImAttribute(itemTag, pathway, ecoName, imName):
  if ecoName in pathway:
    value = pathway[ecoName]
    if isinstance(value, list):
      value = value[0]
  else:
    value = ''

  return ET.SubElement(itemTag, "attribute", attrib = { "name" : imName, "value" : value })

############
### MAIN ###
############
parser = MyParser('Tranform ecocyc pathways flat files to InterMine items import XML.')
parser.add_argument('inputDirname', help='the directory containing the input flat files.')
parser.add_argument('outputFilename', help='the output location for the generated items XML.')
args = parser.parse_args()

pathwaysDatFn = "pathways.dat"

if not os.path.isdir(args.inputDirname):
  print >> sys.stderr, "[%s] is not a directory" % args.inputDirname
  sys.exit(1)

inputDirname = args.inputDirname
outputFilename = args.outputFilename
pathways = {}

with open("%s/%s" % (inputDirname, pathwaysDatFn)) as f:
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

      print "Processing pathway %s" % value

      pathway = {}

    # Add value to key entry
    if not key in pathway:
      pathway[key] = []

    pathway[key].append(value)

    lastKey = key

if pathway != None:
  print >> sys.stderr, "Finished processing %s but still in unclosed pathway %s" % (pathwaysDatFn, pathway['UNIQUE-ID'])
  sys.exit(1)

print "Processed %d pathways" % len(pathways)

# Yeah, we should write the python equivalent for the perl api here but for now let's be lazy
itemsTag = ET.Element("items")
i = 1

for pathway in pathways.itervalues():
  print "Writing pathway %s" % (pathway['UNIQUE-ID'][0])

  itemTag = ET.SubElement(itemsTag, "item", attrib = { "id" : "0_%d" % (i), "class" : "Pathway", "implements" : "" })
  addImAttribute(itemTag, pathway, 'UNIQUE-ID', 'identifier')
  addImAttribute(itemTag, pathway, 'COMMON-NAME', 'name')
  addImAttribute(itemTag, pathway, 'COMMENT', 'description')
  i += 1

tree = ET.ElementTree(itemsTag)
tree.write(outputFilename, pretty_print=True)
