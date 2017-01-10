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
    'geo',
    [
        imp.Source(
            'faith-GEOSeries-EcoliK12', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/current/geo/load/faith-2007' },
            ]),
        imp.Source(
            'nicolas2012-GEOSeries-Bsub168', 'synbio-GEOSeries',
            [
                { 'name':'src.data.dir',        'location':'data/current/geo/load/nicolas-2012' },
            ])
    ])
