#!/usr/bin/env python3

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.project as imp
import synbio.utils as sbu

############
### MAIN ###
############
sbu.handleSimpleSourceAddProcess(
    "ecocyc",
    [
        imp.Source(
            'synbio-ecocyc', 'synbio-ecocyc',
            [
                { 'name':'src.data.dir',        'location':'data/current/ecocyc' },
            ])
    ])