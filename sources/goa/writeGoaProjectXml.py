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
    'goa',
    [
        imp.Source(
            'go-annotation', 'go-annotation',
            [
                { 'name':'src.data.dir',        'location':'{{imDataPath}}/goa/load' },
            ])
    ])
