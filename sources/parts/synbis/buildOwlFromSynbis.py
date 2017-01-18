#!/usr/bin/env python3

import glob
import jargparse
import os
import owlready
import rdflib
from rdflib.namespace import RDF
import sys
import types as typs
import urllib.parse as up

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import intermyne.utils as imu
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def addPropertiesFromRdf(graph, props, instance):
    triples = graph.triples((instance, None, None))
    for _, p, _ in triples:
        if p not in props:
            print('Adding [%s]' % p)
            props[generateImName(str(p))] = 1


def generateImName(rdfName):
    """
    We're gonna do something super hacky and generate InterMine names from RDF URLs by welding the first dotted part
    of the host name to the last part or fragment (if available) of the path
    """

    _, host, path, _, _, fragment = up.urlparse(rdfName)
    a = host.split('.')[0]
    if fragment != '':
        b = fragment
    else:
        b = path.split('/')[-1]

    return a + b

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

onto = owlready.Ontology('http://intermine.org/synbiomine/synbis.owl')

graph = rdflib.Graph()

for partsPath in glob.glob(ds.getRawPath() + 'parts/*.xml'):
    imu.printSection('Analyzing ' + partsPath)
    with open(partsPath) as f:
        graph.load(f)

# print(graph.serialize(format='turtle').decode('unicode_escape'))

types = {}

typeTriples = graph.triples((None, RDF.type, None))
for instance, _, type in typeTriples:
    if type not in types:
        types[type] = {}
    props = types[type]
    addPropertiesFromRdf(graph, props, instance)

for typeName, props in sorted(types.items()):
    imTypeName = generateImName(typeName)
    print(', '.join((typeName, imTypeName)))

    for p in props:
        print('  ' + p)

    typs.new_class(imTypeName, (owlready.Thing,), kwds = { "ontology" : onto })

# print(owlready.to_owl(onto))
