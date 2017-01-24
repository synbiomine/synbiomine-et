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
    'biogrid',
    [
        imp.Source(
            'biogrid', 'biogrid',
            [
                { 'name':'src.data.dir',            'location':'{{imDataPath}}/biogrid/load' },
                { 'name':'src.data.dir.includes',   'value':'*psi25.xml'},
                { 'name':'biogrid.organisms',       'value':'511145 224308'}
            ])
    ])
