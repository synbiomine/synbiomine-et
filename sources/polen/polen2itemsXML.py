#!/usr/bin/env python

import glob
import os
import sys
import lxml.etree as et

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import synbio.data as sbd

###############
### CLASSES ###
###############
class Part:
    def Part(self, name, displayName, type, description, sequence, organism, designMethod):
        self.name = name
        self.displayName = displayName
        self.type = type
        self.description = description
        self.sequence = sequence
        self.organism = organism
        self.designMethod = designMethod

#################
### FUNCTIONS ###
#################
"""
Given a set of parts, output InterMine items XML.
"""
def outputPartsToItemsXml(ds, parts):
    model = ds.getCollection().getModel()
    doc = imm.Document(model)

    imu.printSection('Adding metadata items')
    dataSourceItem = doc.createItem('DataSource')
    dataSourceItem.addAttribute('name', 'POLEN')
    dataSourceItem.addAttribute('url', 'http://intbio.ncl.ac.uk/?projects=polen')
    doc.addItem(dataSourceItem)

    dataSetItem = doc.createItem('DataSet')
    dataSetItem.addAttribute('name', 'POLEN Parts')
    dataSetItem.addAttribute('dataSource', dataSourceItem)
    doc.addItem(dataSetItem)

    imu.printSection('Adding %d part items' % (len(parts)))
    for part in parts.values():
        partItem = doc.createItem('Part')
        partItem.addAttribute('name', part['Name'])
        partItem.addAttribute('type', part['Type'])
        partItem.addAttribute('description', part['Description'])

        # XXX: Reconstructing the uri here is heavily less than ideal
        partItem.addAttribute('uri', 'http://www.virtualparts.org/part/%s' % part['Name'])

        partItem.addAttribute('organism', part['Organism'])
        partItem.addAttribute('designMethod', part['DesignMethod'])

        # Sequence in all virtualparts.org XML has a mangled CDATA tag.
        # Let's see if Newcastle fix this before taking demangling measures ourselves
        # partItem.addAttribute('sequence', part['Sequence'])

        partItem.addToAttribute('dataSets', dataSetItem)
        doc.addItem(partItem)

    doc.write('%s/items.xml' % ds.getLoadPath())

############
### MAIN ###
############
parser = imu.ArgParser('Transform POLEN data into InterMine items XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')

parts = {}

rawPartsXmlPaths = glob.glob("%s/parts/*.xml" % ds.getRawPath())
for rawPartXmlPath in rawPartsXmlPaths:
    partE = et.parse(rawPartXmlPath).getroot()
    name = partE.find('Name').text

    if name in parts:
        print "When processing %s already found part with name %s.  Ignoring." % (rawPartXmlPath, name)
        continue

    data = {
        'Name' : name,
        'Type' : partE.find('Type').text,
        'Description' : partE.find('Description').text,
        'Organism' : partE.find('Organism').text,
        'DesignMethod' : partE.find('DesignMethod').text,
        'Sequence' : partE.find('Sequence').text
    }

    parts[name] = data

outputPartsToItemsXml(ds, parts)
