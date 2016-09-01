#!/usr/bin/env python

import jargparse
import os
import sys

import vprim

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.utils as imu
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def validatePartsProperty(parts, propName):
    """
    Show counts for the given part property
    """

    imu.printSection('Validating VPR part %ss' % propName)

    propValues = {}

    for part in parts.values():
        if propName in part:
            propValue = part[propName]

            if propValue in propValues:
                propValues[propValue] += 1
            else:
                propValues[propValue] = 1

        else:
            print 'Part %s has no %s data' % (part['Name'], propName)

    print 'Found distinct %s names:' % propName
    for name, count in propValues.iteritems():
        print "%s: %d" % (name, count)

############
### MAIN ###
############
parser = jargparse.ArgParser('Validate VPR parts and list information on various fields.')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

parts = vprim.loadPartsFromXml(ds)
validatePartsProperty(parts, 'Type')
validatePartsProperty(parts, 'Organism')
