#!/usr/bin/env python

import glob
import jargparse
import os
import sys
import xmltodict

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import jbio.sources.go as go
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
        with open(rawPartXmlPath) as f:
            partE = xmltodict.parse(f, force_list=('Property',))['Part']

        name = partE['Name']

        if name in parts:
            print "When processing %s already found part with name %s" % (rawPartXmlPath, name)
        else:
            parts[name] = partE

    return parts

"""
Given a set of parts, output InterMine items XML.
"""
def outputPartsToItemsXml(ds, goDs, parts):
    # We need to get a dictionary of go synonyms so that we can resolve those used in virtualparts
    imu.printSection('Loading GO synonyms')
    goSynonyms = go.getSynonoyms("%s/%s" % (goDs.getLoadPath(), 'go-basic.obo'))

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

    imu.printSection('Adding part items')
    print 'Adding %d parts' % (len(parts))

    for part in parts.values():
        name = part['Name']
        partItem = doc.createItem('Part')
        partItem.addAttribute('name', name)
        partItem.addAttribute('type', part['Type'])
        partItem.addAttribute('description', part['Description'])

        # XXX: Reconstructing the uri here is heavily less than ideal
        partItem.addAttribute('uri', 'http://www.virtualparts.org/part/%s' % name)

        partItem.addAttribute('organism', part['Organism'])
        partItem.addAttribute('designMethod', part['DesignMethod'])

        # Sequence in all virtualparts.org XML has a mangled CDATA tag.
        # Let's see if Newcastle fix this before taking demangling measures ourselves
        # partItem.addAttribute('sequence', data['Sequence'])


        for propertyComponents in part['Property']:
            name = propertyComponents['Name']
            value = propertyComponents['Value']

            if name == 'has_function':
                partItem.addToAttribute('functions', createGoTermItem(doc, partItem, value, goSynonyms, 'has_function'))
            elif name == 'participates_in':
                partItem.addToAttribute('participatesIn', createGoTermItem(doc, partItem, value, goSynonyms, 'participates_in'))

        partItem.addToAttribute('dataSets', dataSetItem)
        doc.addItem(partItem)

    doc.write('%s/items.xml' % ds.getLoadPath())

def createGoTermItem(doc, partItem, id, goSynonyms, originalAttributeName):
    # For some ineffable reason, virtualparts uses _ in their go term IDs rather than GO's own :
    id = id.replace('_', ':')

    if id in goSynonyms:
        print 'Replacing %s synonym %s with %s for part %s' % (originalAttributeName, id, goSynonyms[id], partItem.getAttribute('name'))
        id = goSynonyms[id]

    goTermItem = doc.createItem('GOTerm')
    goTermItem.addAttribute('identifier', id)
    doc.addItem(goTermItem)

    return goTermItem

############
### MAIN ###
############
parser = jargparse.ArgParser('Transform POLEN data into InterMine items XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

outputPartsToItemsXml(ds, dc.getSet('go'), processXmlToParts(ds))
