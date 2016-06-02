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
    "GEO",
    [
        imp.Source(
            'faith-GEOSeries-EcoliK12', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/geo/faith-2007' },
            ]),
        imp.Source(
            'nicolas2012-GEOSeries-Bsub168', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/geo/nicolas-2012' },
            ])
    ],
    "writeGeoProjectXml")