#!/usr/bin/env python3

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.project as imp
import intermyne.utils as imu

############
### MAIN ###
############
imu.handleSimpleSourceAddProcess(
    "Polen",
    [
        imp.Source(
            'synbio-polen', 'synbio-polen',
            [
                { 'name':'src.data.dir',        'location':'data/polen/load' },
            ])
    ],
    "writePolenProjectXml")