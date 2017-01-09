#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.project as imp
import intermyne.utils as imu

############
### MAIN ###
############
imu.handleSimpleSourceAddProcess(
    "Ecocyc",
    [
        imp.Source(
            'synbio-ecocyc', 'synbio-ecocyc',
            [
                { 'name':'src.data.dir',        'location':'data/current/ecocyc' },
            ])
    ],
    "writeEcocycProjectXml")