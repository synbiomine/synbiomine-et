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
    "GO Annotation",
    [
        imp.Source(
            'go-annotation', 'go-annotation',
            [
                { 'name':'src.data.dir',        'location':'data/goa' },
            ])
    ],
    "writeGoaProjectXml")