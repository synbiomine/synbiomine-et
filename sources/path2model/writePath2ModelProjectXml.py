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
    'path2model',
    [
        imp.Source(
            'pathway2model-Bsub168', 'synbio-reaction',
            [
                { 'name':'src.data.dir',        'location':'data/current/path2model/load/Bsub168' },
            ]),
        imp.Source(
            'pathway2model-EcoliMG1655', 'synbio-reaction',
            [
                { 'name':'src.data.dir',        'location':'data/current/path2model/load/EcoliMG1655' },
            ])
    ])
