#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.project as imp
import intermyne.utils as imu

############
### MAIN ###
############
imu.handleSimpleSourceAddProcess(
    'Gene Ontology',
    [
        imp.Source(
            'go', 'go',
            [
                { 'name':'src.data.file',        'location':'data/go/load/gene_ontology.obo' },
            ])
    ],
    "writeGoProjectXml")