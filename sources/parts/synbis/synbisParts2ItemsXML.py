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
def addPartItem(doc, componentUrl, graph, organismItems, sequenceItems, soTermItems, dsItem):

    partItemMap = {
        'http://sbols.org/v2#displayId':'name',
        'http://sbols.org/v2#persistentIdentity':'uri',
        'http://sbols.org/v2#role':'role',
        'http://sbols.org/v2#sequence':'sequence',
        'http://sbols.org/v2#type':'type',
        'http://synbis.bg.ic.ac.uk/nativeFrom':'organism',
        'http://synbis.bg.ic.ac.uk/origin':'origin',
        'http://synbis.bg.ic.ac.uk/rnapSpecies':'rnapSpecies',
        'http://synbis.bg.ic.ac.uk/rnapSigmaFactor':'rnapSigmaFactor'
    }

    partItem = doc.createItem('SynBioPart')
    partItem.addToAttribute('dataSets', dsItem)

    query = 'SELECT ?p ?o WHERE { <%s> ?p ?o . }' % componentUrl
    # print(query)
    rows = graph.query(query)

    for p, o in rows:
        o = str(o)
        p = str(p)

        if p in partItemMap:
            if p == 'http://sbols.org/v2#role':
                soTerm = o.split('/')[-1]
                print('Got SOTerm [%s]' % soTerm)
                if soTerm not in soTermItems:
                    soTermItems[soTerm] = addSoTermItem(doc, soTerm)
                partItem.addAttribute('role', soTermItems[soTerm])
            elif p == 'http://synbis.bg.ic.ac.uk/nativeFrom':
                print('Got organism [%s]' % o)
                if o != '':
                    if o not in organismItems:
                        organismItems[o] = addOrganismItem(doc, o)
                    partItem.addAttribute('organism', organismItems[o])
            elif p == 'http://sbols.org/v2#sequence':
                if o in sequenceItems:
                    partItem.addAttribute('sequence', sequenceItems[o])
                else:
                    raise Exception('Sequence %s specified for %s but no matching InterMine sequence item exists' % (o, componentUrl))
            else:
                partItem.addAttribute(partItemMap[p], o)
        else:
            print('Ignoring (%s, %s) as not found in item map' % (p, o))

    doc.addItem(partItem)

    return partItem

def addSequenceItem(doc, url, graph):

    itemMap = {
        'http://sbols.org/v2#encoding':'encoding',
        'http://sbols.org/v2#elements':'residues'
    }

    item = doc.createItem('SynBioSequence')

    query = 'SELECT ?p ?o WHERE { <%s> ?p ?o . }' % url
    rows = graph.query(query)

    for p, o in rows:
        o = str(o)
        p = str(p)

    if p in itemMap:
        item.addAttribute(itemMap[p], o)
    else:
        print('Ignoring (%s, %s) as not found in item map' % (p, o))

    doc.addItem(item)

    return item


def addOrganismItem(doc, synbisName):
    SYNBIS_NATIVEFROM_NAMES_TO_TAXON_IDS = {
        'E. coli': 562
    }

    item = doc.createItem('Organism')
    if synbisName in SYNBIS_NATIVEFROM_NAMES_TO_TAXON_IDS:
        taxonId = SYNBIS_NATIVEFROM_NAMES_TO_TAXON_IDS[synbisName]
    else:
        taxonId = 0

    item.addAttribute('taxonId', taxonId)
    doc.addItem(item)

    return item

def addSoTermItem(doc, id):
    item = doc.createItem('SOTerm')
    item.addAttribute('identifier', id)
    doc.addItem(item)

    return item

def addRdfItems(type, doc, graph):
    imItems = {}
    rdfItems = graph.triples((None, RDF.type, rdflib.term.URIRef(type)))
    for url, _, _ in rdfItems:
        url = str(url)
        if url not in imItems:
            print('Adding %s to imItems' % url)
            imItems[url] = addSequenceItem(doc, url, graph)

    return imItems

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
organismItems = {}
soTermItems = {}

for partsPath in glob.glob(ds.getRawPath() + 'parts/*.xml'):
    print('Analyzing ' + partsPath)
    with open(partsPath) as f:
        g = rdflib.Graph()
        g.load(f)
        # print(g.serialize(format='turtle').decode('unicode_escape'))

        sequenceItems = addRdfItems('http://sbols.org/v2#Sequence', doc, g)

        componentDefinitions = g.triples((None, RDF.type, rdflib.term.URIRef('http://sbols.org/v2#ComponentDefinition')))
        # rows = g.query('SELECT ?s ?p ?o WHERE { ?s a sbol:ComponentDefinition . }')
        # componentDefinitions = g.triples((None, rdflib.namespace.RDF.type, None))
        #print(sum(1 for _ in componentDefinitions))
        for componentUrl, _, _ in componentDefinitions:
            componentUrl = str(componentUrl)
            if componentUrl not in partItems:
                print('Adding %s to parts list' % componentUrl)
                partItems[componentUrl] = addPartItem(doc, componentUrl, g, organismItems, sequenceItems, soTermItems, dataSetItem)
            # else:
                # print('Skipping %s as already in parts list' % componentUrl)

if not args.dummy:
    doc.write(ds.getLoadPath() + 'items.xml')
