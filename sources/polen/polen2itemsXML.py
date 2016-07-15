#!/usr/bin/env python

import glob
import os
import sys
import lxml.etree as et

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
"""
Given a dataset, process all the POLEN parts xml here to our internal parts representations
"""
def processXmlToParts(ds):
    parts = {}

    rawPartsXmlPaths = glob.glob("%s/parts/*.xml" % ds.getRawPath())
    for rawPartXmlPath in rawPartsXmlPaths:
        partE = et.parse(rawPartXmlPath).getroot()
        name = partE.find('Name').text

        if name in parts:
            print "When processing %s already found part with name %s.  Ignoring." % (rawPartXmlPath, name)
            continue

        data = {}
        properties = []

        for childE in partE:
            if childE.tag == 'Property':
                propertyComponents = {}
                for propertyComponentE in childE:
                    print "Adding %s:%s" % (propertyComponentE.tag, propertyComponentE.text)
                    propertyComponents[propertyComponentE.tag] = propertyComponentE.text

                properties.append(propertyComponents)

            data[childE.tag] = childE.text

        parts[name] = { 'data': data, 'properties' : properties }

    return parts

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
        data = part['data']
        partItem = doc.createItem('Part')
        partItem.addAttribute('name', data['Name'])
        partItem.addAttribute('type', data['Type'])
        partItem.addAttribute('description', data['Description'])

        # XXX: Reconstructing the uri here is heavily less than ideal
        partItem.addAttribute('uri', 'http://www.virtualparts.org/part/%s' % data['Name'])

        partItem.addAttribute('organism', data['Organism'])
        partItem.addAttribute('designMethod', data['DesignMethod'])

        # Sequence in all virtualparts.org XML has a mangled CDATA tag.
        # Let's see if Newcastle fix this before taking demangling measures ourselves
        # partItem.addAttribute('sequence', data['Sequence'])

        for propertyComponents in part['properties']:
            name = propertyComponents['Name']
            value = propertyComponents['Value']

            if name == 'has_function':
                partItem.addToAttribute('functions', createGoTermItem(doc, value))
            elif name == 'participates_in':
                partItem.addToAttribute('participatesIn', createGoTermItem(doc, value))

        partItem.addToAttribute('dataSets', dataSetItem)
        doc.addItem(partItem)

    doc.write('%s/items.xml' % ds.getLoadPath())

def createGoTermItem(doc, id):
    goTermItem = doc.createItem('GOTerm')

    # For some ineffable reason, virtualparts uses _ in their go term IDs rather than GO's own :
    goTermItem.addAttribute('identifier', id.replace('_', ':'))

    doc.addItem(goTermItem)
    return goTermItem

############
### MAIN ###
############
parser = imu.ArgParser('Transform POLEN data into InterMine items XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

outputPartsToItemsXml(ds, processXmlToParts(ds))
