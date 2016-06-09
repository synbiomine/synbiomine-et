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
    "InterPro",
    [
        imp.Source(
            'interpro', 'interpro',
            [
                { 'name':'src.data.dir',            'location':'/micklem/data/interpro/current' },
            ]),

        imp.Source(
            'protein2ipr', 'protein2ipr',
            [
                { 'name':'src.data.dir',            'location':'/micklem/data/interpro/match_complete' },
                { 'name':'src.data.dir.includes',   'value':'protein2ipr.dat' }
            ])
    ],
    "writeInterProProjectXml")