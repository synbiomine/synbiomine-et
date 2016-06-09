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
    "path2model",
    [
        imp.Source(
            'pathway2model-Bsub168', 'synbio-reaction',
            [
                { 'name':'src.data.dir',        'location':'data/current/path2model/Bsub168' },
            ]),
        imp.Source(
            'pathway2model-EcoliMG1655', 'synbio-reaction',
            [
                { 'name':'src.data.dir',        'location':'data/current/path2model/EcoliMG1655' },
            ])
    ],
    "writePath2ModelProjectXml")