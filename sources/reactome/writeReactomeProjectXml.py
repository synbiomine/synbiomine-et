#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.project as imp
import synbio.utils as sbu

############
### MAIN ###
############
sbu.handleSimpleSourceAddProcess(
    'reactome',
    [
        imp.Source(
            'reactome', 'reactome',
            [
                { 'name':'src.data.dir',            'location':'/micklem/data/reactome/current' },
                { 'name':'reactome.organisms',      'value':'511145'},
                { 'name':'reactome.datasourcename', 'value':'Reactome'},
                { 'name':'reactome.datasetname',    'value':'Reactome data set'},
                { 'name':'reactome.curated',        'value':'false'}
            ])
    ])
