#!/usr/bin/env python3

import glob
import jargparse
import os
import owlready
import rdflib
from rdflib.namespace import RDF
import synbisConfig
import synbisUtils
import sys
import types as typs

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
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
    imTypeName = synbisUtils.generateImClassName(type, synbisConfig.rdfNsToImName)
    if imTypeName not in imTypes:
        imTypes[imTypeName] = typs.new_class(imTypeName, (owlready.Thing,), kwds = {'ontology':onto})

# For every instance:
typeTriples = graph.triples((None, RDF.type, None))
for instance, _, type in typeTriples:
    # print('Processing type %s' % type)

    instanceTriples = graph.triples((instance, None, None))

    # For every property of an instance:
    for _, p, o in instanceTriples:

        # We don't want to translate the properties that are just signalling instanceof in the RDF
        if p == RDF.type:
            continue

        imTypeName = synbisUtils.generateImClassName(type, synbisConfig.rdfNsToImName)
        imPropName = synbisUtils.generateImPropertyName(str(p), synbisConfig.rdfNsToImName)
        imType = imTypes[imTypeName]

        if imTypeName == 'SynBISProtocol' and imPropName == 'SynBIS_definition':
            # We're going to skip this multi-range property temporarily until we have other things working
            imu.printWarning('Skipping %s.%s' % (imTypeName, imPropName))
            continue

        if imTypeName == 'SynBISTransferFunction' and imPropName == 'SynBIS_modality':
            # the synbis_modality property is a reference in some places but just a string in others!
            # this might be a problem with the synbis data model
            # We're going to skip this temporarily until we get other things working (a fix may be doing some post
            # download editing on the synbis rdf
            imu.printWarning('Skipping %s.%s' % (imTypeName, imPropName))
            continue

        if imPropName not in imProps:
            print('  Adding property %s.%s' % (imTypeName, imPropName))
            imProps[imPropName] = typs.new_class(imPropName, (owlready.Property,), kwds = {'ontology':onto})

        imProp = imProps[imPropName]

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
        if isinstance(o, rdflib.term.URIRef) and not str(p) == 'http://sbols.org/v2#persistentIdentity':
            # See if this URI matches the ID of any internal instance
            objectTypeTriples = graph.triples((o, RDF.type, None))

            # Only progress for URLs that are instance IDs within this document
            try:
                objectTypeName = next(objectTypeTriples)[2]
            except StopIteration:
                continue

            objectImTypeName = synbisUtils.generateImClassName(objectTypeName, synbisConfig.rdfNsToImName)
            if objectImTypeName in imTypes:
                #print('Got %s' % objectImTypeName)
                objectImType = imTypes[objectImTypeName]

                if objectImType not in imProp.range:
                    print('  Adding range type %s for %s.%s' % (objectImType, instance, p))
                    imProp.range.append(objectImType)

                    if len(imProp.range) > 1:
                        imu.printWarning('Range for %s.%s now has %d entities, %s' % (imTypeName, imPropName, len(imProp.range), imProp.range))
            else:
                imu.printError('Found %s but not in imTypes' % objectImTypeName)

with open(ds.getProcessingPath() + 'synbis.owl', 'w') as f:
    f.write(owlready.to_owl(onto))
