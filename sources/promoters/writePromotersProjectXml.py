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
    'promoters',
    [
        imp.Source(
            'dbtbs-regulation-Bsub168', 'synbio-regulation',
            [
                { 'name':'src.data.dir',        'location':'data/current/promoters/load/dbtbs' },
            ]),
        imp.Source(
            'nicolas2012-regulation-Bsub168', 'synbio-regulation',
            [
                { 'name':'src.data.dir',        'location':'data/current/promoters/load/nicolas-2012' },
            ])
    ])
