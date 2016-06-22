#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.project as imp
import intermyne.utils as imu

############
### MAIN ###
############
imu.handleSimpleSourceAddProcess(
    "Biogrid",
    [
        imp.Source(
            'biogrid', 'biogrid',
            [
                { 'name':'src.data.dir',            'location':'data/current/biogrid' },
                { 'name':'src.data.dir.includes',   'value':'*psi25.xml'},
                { 'name':'biogrid.organisms',       'value':'511145 224308'}
            ])
    ],
    "writeBiogridProjectXml")