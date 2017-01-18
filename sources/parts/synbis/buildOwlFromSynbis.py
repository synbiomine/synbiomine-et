#!/usr/bin/env python3

import glob
import jargparse
import os
import owlready as owr
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
def generateImTypeName(rdfTypeName):
    """
    We're gonna do something super hacky and generate the InterMine class name as a compound of the first dotted part
    of the host name and the type name
    """

    _, host, path, _, _, fragment = up.urlparse(rdfTypeName)
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

graph = rdflib.Graph()

for partsPath in glob.glob(ds.getRawPath() + 'parts/*.xml'):
    imu.printSection('Analyzing ' + partsPath)
    with open(partsPath) as f:
        graph.load(f)

types = {}

typeTriples = graph.triples((None, RDF.type, None))
for _, _, type in typeTriples:
    if type not in types:
        types[type] = 1

for type, _ in sorted(types.items()):
    print(', '.join([type, generateImTypeName(type)]))

# print(g.serialize(format='turtle').decode('unicode_escape'))

"""
onto = owr.Ontology('http://dummy.owl')
print(owr.to_owl(onto))
"""