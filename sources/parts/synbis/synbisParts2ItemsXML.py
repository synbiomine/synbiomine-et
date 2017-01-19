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

for name, _, type in rdfInstanceOfTriples:
    if name not in items:
        # This may not be a good way to get an InterMine suitable name from an url
        imTypeName = synbisUtils.generateImName(type)
        items[name] = doc.createItem(imTypeName)
        doc.addItem(items[name])
    item = items[name]

    propTriples = graph.triples((name, None, None))
    for _, p, o in propTriples:
        if p == RDF.type:
            continue
        elif not isinstance(o, rdflib.term.URIRef):  # external edges will not be of type rdflib.term.URIRef
            imPropName = synbisUtils.generateImName(str(p))
            item.addAttribute(imPropName, o)

#print(doc)
doc.write(ds.getLoadPath() + 'items.xml')

#item = doc.createItem(name)

# print(graph.serialize(format='turtle').decode('unicode_escape'))