#!/usr/bin/env python3

import jargparse
from lxml import etree
import os
import owlready
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../../modules/python')
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Convert OWL to InterMine model XML')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-d', '--dummy', action='store_true', help='dummy run, do not store anything')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('parts/synbis')
ds.startLogging(__file__)

owlready.onto_path.append(ds.getProcessingPath())
synbisOnto = owlready.get_ontology('http://intermine.org/synbiomine/synbis.owl').load()

classes_e = etree.Element('classes')

for owlClass in synbisOnto.classes:
    print(owlClass)
    class_e = etree.SubElement(classes_e, 'class', { 'name':str(owlClass), 'is-interface':'true' })

    # very inefficient but not sure if there is an easier way to do this yet
    for owlProp in synbisOnto.properties:
        if owlClass in owlProp.domain:
            if len(owlProp.range) == 0:
                etree.SubElement(class_e, 'attribute', { 'name':str(owlProp), 'type':'java.lang.String' })
            else:
                etree.SubElement(class_e, 'reference', { 'name':str(owlProp), 'referenced-type':str(owlProp.range[0]) })

    # TODO: should be in config
    if str(owlClass) == 'synbisDatasheet':
        etree.SubElement(class_e, 'collection', { 'name':'dataSet', 'referenced-type':'DataSet' })

#print(etree.tostring(classes_e, pretty_print=True).decode('unicode_escape'))
#print(owlready.to_owl(synbisOnto))

etree.ElementTree(classes_e).write(ds.getProcessingPath() + 'synbio-synbis_additions.xml', pretty_print=True)
