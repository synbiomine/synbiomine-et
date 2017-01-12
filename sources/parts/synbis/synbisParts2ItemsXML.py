#!/usr/bin/env python3

import glob
import jargparse
import os
import rdflib
from rdflib.namespace import RDF
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import intermyne.metadata as immd
import intermyne.model as imm
import synbio.data as sbd

#################
### FUNCITONS ###
#################
def addPartItem(doc, componentUrl, graph, soTermItems, dsItem):

    partItem = doc.createItem('Part')
    partItem.addToAttribute('dataSets', dsItem)

    query = 'SELECT ?p ?o WHERE { <%s> ?p ?o . }' % componentUrl
    # print(query)
    rows = graph.query(query)

    for p, o in rows:
        if p == rdflib.term.URIRef('http://sbols.org/v2#displayId'):
            partItem.addAttribute('name', o)
        elif p == rdflib.term.URIRef('http://sbols.org/v2#persistentIdentity'):
            partItem.addAttribute('uri', o)
        elif p == rdflib.term.URIRef('http://sbols.org/v2#role'):
            soTerm = o.split('/')[-1]
            print('Got SOTerm [%s]' % soTerm)
            if soTerm not in soTermItems:
                soTermItems[soTerm] = addSoTermItem(doc, soTerm)
            partItem.addAttribute('role', soTerm)

    doc.addItem(partItem)

    return partItem

def addSoTermItem(doc, id):

    item = doc.createItem('SOTerm')
    item.addAttribute('identifier', id)
    doc.addItem(item)

    return item

############
### MAIN ###
############
parser = jargparse.ArgParser('Take raw data downloaded from synbis and turn into InterMine Item XML.')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-d', '--dummy', action='store_true', help='dummy run, do not store anything')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

model = dc.getModel()
doc = imm.Document(model)
dataSourceItem = immd.addDataSource(doc, 'SynBIS', 'http://synbis.bg.ic.ac.uk')
dataSetItem = immd.addDataSet(doc, 'SYNBIS parts', dataSourceItem)

partItems = {}
soTermItems = {}

for partsPath in glob.glob(ds.getRawPath() + 'parts/*.xml'):
    print('Analyzing ' + partsPath)
    with open(partsPath) as f:
        g = rdflib.Graph()
        g.load(f)
        # print(g.serialize(format='turtle').decode('unicode_escape'))
        componentDefinitions = g.triples((None, RDF.type, rdflib.term.URIRef('http://sbols.org/v2#ComponentDefinition')))
        # rows = g.query('SELECT ?s ?p ?o WHERE { ?s a sbol:ComponentDefinition . }')
        # componentDefinitions = g.triples((None, rdflib.namespace.RDF.type, None))
        #print(sum(1 for _ in componentDefinitions))
        for componentDefinition in componentDefinitions:
            # print(componentDefinition)
            for componentUrl, _, _ in componentDefinitions:
                if componentUrl not in partItems:
                    print('Adding %s to parts list' % componentUrl)
                    partItems[componentUrl] = addPartItem(doc, componentUrl, g, soTermItems, dataSetItem)
                # else:
                    # print('Skipping %s as already in parts list' % componentUrl)

if not args.dummy:
    doc.write(ds.getLoadPath() + 'items.xml')
