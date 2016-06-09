#!/usr/bin/python

import os
import sys
import urllib

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.model as IM
import intermine.utils as imu

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

#Based on an answer by John Machin on Stack Overflow (http://stackoverflow.com/users/84270/john-machin)
#http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
# However, adapted to also filter out extended ASCII (0x7f to 0xff).  May be a better way of doing this.
def isValidXMLChar(char):
  codepoint = ord(char)
  return 0x20 <= codepoint <= 0x7E or   \
         0x100 <= codepoint <= 0xD7FF or   \
         codepoint in (0x9, 0xA, 0xD) or  \
         0xE000 <= codepoint <= 0xFFFD or \
         0x10000 <= codepoint <= 0x10FFFF

def filterInvalidXMLChars(input):
    return filter(isValidXMLChar, input)

############
### MAIN ###
############
parser = imu.ArgParser('Tranform ecocyc pathways flat files to InterMine items import XML')
parser.add_argument('datasetPath', help='path to the dataset location')
args = parser.parse_args()

# This contains pathway details
pathwaysDatFn = "pathways.dat"

# This links gene ids to pathways
pathwaysColFn = "pathways.col"

datasetPath = args.datasetPath
model = IM.Model('%s/intermine/genomic_model.xml' % datasetPath)
doc = IM.Document(model)
inputDn = "%s/ecocyc" % datasetPath
outputFn = "%s/ecocyc/items.xml" % datasetPath

if not os.path.isdir(inputDn):
  print >> sys.stderr, "[%s] is not a directory" % inputDn
  sys.exit(1)

pathways = processPathwaysDatFile("%s/%s" % (inputDn, pathwaysDatFn))
pathwaysToGenes = processPathwaysColFile("%s/%s" % (inputDn, pathwaysColFn))

print "Processed %d pathways" % len(pathways)

imu.printSection("Adding metadata items")
dataSourceItem = doc.createItem("DataSource")
dataSourceItem.addAttribute('name', 'Ecocyc')
dataSourceItem.addAttribute('url', 'http://ecocyc.org')
doc.addItem(dataSourceItem)

dataSetItem = doc.createItem("DataSet")
dataSetItem.addAttribute('name', 'Ecocyc pathways')
dataSetItem.addAttribute('dataSource', dataSourceItem)
doc.addItem(dataSetItem)

imu.printSection("Adding organism item")
organismItem = doc.createItem("Organism")

# NCBI Taxon id for Escherichia coli K-12 substr. MG1655
organismItem.addAttribute('taxonId', 511145)
doc.addItem(organismItem)

imu.printSection("Adding pathway items")

# We need to track pathway IM items so we can later associate these with genes
pathwayItems = {}

for pathway in pathways.itervalues():
  # print "Writing pathway %s" % (pathway['UNIQUE-ID'][0])
  pathwayId = pathway['UNIQUE-ID'][0]
  pathwayName = pathway['COMMON-NAME'][0]

  pathwayItem = doc.createItem("Pathway")
  pathwayItem.addAttribute('identifier', pathwayId)
  pathwayItem.addAttribute('name', pathwayName)

  if 'COMMENT' in pathway:
    pathwayComment = pathway['COMMENT'][0]
  else:
    pathwayComment = ''

  pathwayItem.addAttribute('description', filterInvalidXMLChars(pathwayComment))
  # pathwayItem.addAttribute('description', pathwayComment.decode('iso-8859-1').encode('utf8'))
  pathwayItem.addToAttribute('dataSets', dataSetItem)

  doc.addItem(pathwayItem)
  pathwayItems[pathwayId] = pathwayItem

imu.printSection("Adding gene items")

geneItems = {}

for pathway in pathwaysToGenes.itervalues():
  # print "Writing %d genes for pathway %s" % (len(pathway['GENE-NAME']), pathway['UNIQUE-ID'][0])

  for symbol in pathway['GENE-NAME']:
    if symbol == '':
      continue

    if not symbol in geneItems:
      # print "Processing symbol %s" % symbol
      geneItem = doc.createItem("Gene")
      geneItem.addAttribute('symbol', symbol)
      geneItem.addAttribute('organism', organismItem)

      doc.addItem(geneItem)
      geneItems[symbol] = geneItem
    else:
      geneItem = geneItems[symbol]
    
    pathwayId = pathway['UNIQUE-ID'][0]

    if pathwayId in pathwayItems:
      pathwayItem = pathwayItems[pathwayId]
      geneItem.addToAttribute('pathways', pathwayItem)
      pathwayItem.addToAttribute('genes', geneItem)
    else:
      print >> sys.stderr, "Gene %s has pathway %s but not such pathway found in %s" % (symbol, pathwayId, pathwaysDatFn)
      sys.exit(1)

imu.printSection("Writing items XML")
doc.write(outputFn)

print "Wrote %d genes in %d pathways" % (len(geneItems), len(pathwayItems))
