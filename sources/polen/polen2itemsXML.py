#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import synbio.data as sbd

############
### MAIN ###
############
parser = imu.ArgParser('Transform POLEN data into InterMine items XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
model = dc.getModel()
doc = imm.Document(model)

imu.printSection("Adding metadata items")
dataSourceItem = doc.createItem("DataSource")
dataSourceItem.addAttribute('name', 'POLEN')
dataSourceItem.addAttribute('url', 'http://intbio.ncl.ac.uk/?projects=polen')
doc.addItem(dataSourceItem)

dataSetItem = doc.createItem("DataSet")
dataSetItem.addAttribute('name', 'POLEN Parts')
dataSetItem.addAttribute('dataSource', dataSourceItem)
doc.addItem(dataSetItem)

# ds = dc.getSet('polen')