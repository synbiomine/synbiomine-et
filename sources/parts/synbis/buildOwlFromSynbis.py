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
parser = jargparse.ArgParser('Take raw data downloaded from synbis and deduce a data model in bastardized OWL form.')
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
imTypes = {}
imProps = {}

typeTriples = graph.triples((None, RDF.type, None))

for _, _, type in typeTriples:
    imTypeName = generateImName(type)
    if imTypeName not in imTypes:
        imTypes[imTypeName] = typs.new_class(imTypeName, (owlready.Thing,), kwds = {'ontology':onto})

typeTriples = graph.triples((None, RDF.type, None))

for instance, _, type in typeTriples:
    instanceTriples = graph.triples((instance, None, None))
    for _, p, o in instanceTriples:

        # We don't want to translate the properties that are just signalling instanceof in the RDF
        if p == RDF.type:
            continue

        imPropName = generateImName(str(p))
        if imPropName not in imProps:
            print('Adding [%s]' % p)
            imProps[imPropName] = typs.new_class(imPropName, (owlready.Property,), kwds = {'ontology':onto})
        imProp = imProps[imPropName]
        imTypeName = generateImName(type)
        imType = imTypes[imTypeName]

        # Add domain if necessary
        if imType not in imProp.domain:
            imProp.domain.append(imType)
        """
        else:
            print('Found OWL type %s for %s' % (imPropName, instance))
        """

        # Add range if necessary
        # FIXME: We really need to only allow 1 here unless/until we implement automatically generating a class
        # hierarchy since we can't have multiple inheritance...
        if isinstance(o, rdflib.term.URIRef):
            objectTypeTriples = graph.triples((instance, RDF.type, None))
            objectTypeName = next(objectTypeTriples)[2]
            objectImTypeName = generateImName(objectTypeName)
            if objectImTypeName in imTypes:
                #print('Got %s' % objectImTypeName)
                objectImType = imTypes[objectImTypeName]

                if objectImType not in imProp.range:
                    imProp.range.append(objectImType)

with open(ds.getLoadPath() + 'synbis.owl', 'w') as f:
    f.write(owlready.to_owl(onto))
