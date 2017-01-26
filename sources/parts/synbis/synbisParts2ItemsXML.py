#!/usr/bin/env python3

import glob
import jargparse
import os
import rdflib
from rdflib.namespace import RDF
import synbisUtils
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import intermyne.model as imm
import intermyne.metadata as immd
import intermyne.utils as imu
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Take raw data downloaded from synbis and deduce a data model in bastardized OWL form.')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-d', '--dummy', action='store_true', help='dummy run, do not store anything')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

graph = rdflib.Graph()

for partsPath in glob.glob(ds.getRawPath() + 'parts/*.xml'):
    imu.printSection('Analyzing ' + partsPath)
    with open(partsPath) as f:
        graph.load(f)

model = dc.getModel()
doc = imm.Document(model)

items = {}
rdfInstanceOfTriples = graph.triples((None, RDF.type, None))

# TODO: Should be in config
dataSourceItem = immd.addDataSource(doc, 'SynBIS', 'http://synbis.bg.ic.ac.uk')
dataSetItem = immd.addDataSet(doc, 'SYNBIS parts', dataSourceItem)

# First pass: create the items
for name, _, type in rdfInstanceOfTriples:
    if name not in items:
        # This may not be a good way to get an InterMine suitable name from an url
        imTypeName = synbisUtils.generateImClassName(type)
        items[name] = doc.createItem(imTypeName)

        # TODO: should be in config
        if imTypeName == 'synbisDatasheet':
            items[name].addToAttribute('dataSets', dataSetItem)

        doc.addItem(items[name])

    item = items[name]

# Second pass: create the attributes and internal links
for name, item in items.items():
    propTriples = graph.triples((name, None, None))
    for _, p, o in propTriples:
        if p == RDF.type:
            continue

        imPropName = synbisUtils.generateImPropertyName(str(p))

        # don't create an internal linkage of sbols_persistentIdentity as a string back to itself, leave as the external
        # uri instead
        if isinstance(o, rdflib.term.URIRef) and o in items and imPropName != 'sbols_persistentIdentity':
            value = items[o]
        else:
            value = str(o)

        item.addAttribute(imPropName, value)

#print(doc)
doc.write(ds.getLoadPath() + 'items.xml')

#item = doc.createItem(name)

# print(graph.serialize(format='turtle').decode('unicode_escape'))