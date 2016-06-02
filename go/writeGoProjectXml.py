#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
imu.handleSimpleSourceAddProcess(
    'Gene Ontology',
    [
        imp.Source(
            'go', 'go',
            [
                { 'name':'src.data.file',        'location':'/micklem/data/go-annotation/current/gene_ontology.obo' },
            ])
    ],
    "writeGoProjectXml")