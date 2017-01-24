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
    'interpro',
    [
        imp.Source(
            'interpro', 'interpro',
            [
                { 'name':'src.data.dir',            'location':'/micklem/data/interpro/current' },
            ]),

        imp.Source(
            'protein2ipr', 'protein2ipr',
            [
                { 'name':'src.data.dir',            'location':'/micklem/data/interpro/match_complete/current' },
                { 'name':'src.data.dir.includes',   'value':'protein2ipr.dat' }
            ])
    ])
