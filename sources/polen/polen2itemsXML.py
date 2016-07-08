#!/usr/bin/env python

import json
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import synbio.data as sbd

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
        partItem.addAttribute('name', part.name)
        partItem.addAttribute('description', part.description)
        partItem.addAttribute('uri', part.uri)
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

outputPartsToItemsXml(ds, polenPartsMetadata)
