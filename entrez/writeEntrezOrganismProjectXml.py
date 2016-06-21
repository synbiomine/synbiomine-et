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
    'Entrez Organism',
    [
        imp.Source(
            'entrez-organism', 'entrez-organism',
            [
                { 'name':'src.data.file',        'location':'build/organisms.xml' },
            ])
    ],
    'writeEntrezOrganismProjectXml')