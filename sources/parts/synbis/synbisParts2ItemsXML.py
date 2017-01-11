#!/usr/bin/env python3

import glob
import jargparse
import os
import rdflib
from rdflib.namespace import RDF
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Take raw data downloaded from synbis and turn into InterMine Item XML.')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

partsPath = ds.getRawPath() + 'parts/'

for partsFilename in glob.glob(partsPath + '*.xml'):
# for partsFilename in os.listdir(partsPath):
# for partsFilename in ['apFAB101.xml']:
    print('Analyzing ' + partsFilename)
    with open(partsFilename) as f:
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
                print(componentUrl)

        query = 'SELECT ?p ?o WHERE { <%s> ?p ?o . }' % componentUrl
        print(query)
        rows = g.query(query)
        print(sum(1 for _ in rows))