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
def validatePartOrgs(parts):
    """
    Show organisms contained in VPR parts
    """

    imu.printSection('Validating VPR part organisms')

    organismNames = {}

    for part in parts.values():
        if 'Organism' in part:
            organismName = part['Organism']

            if organismName in organismNames:
                organismNames[organismName] += 1
            else:
                organismNames[organismName] = 1

        else:
            print 'Part %s has no organism data' % part['Name']

    print "Found distinct organism names:"
    for name, count in organismNames.iteritems():
        print "%s: %d" % (name, count)

def validatePartTypes(parts):
    """
    Show part types in VPR parts

    :param parts:
    :return:
    """

    imu.printSection('Validating VPR part types')

    types = {}

    for part in parts.values():
        if 'Type' in part:
            type = part['Type']

            if type in types:
                types[type] += 1
            else:
                types[type] = 1

        else:
            print 'Part %s has no type data' % part['Name']

    print "Found distinct part names:"
    for name, count in types.iteritems():
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
validatePartOrgs(parts)
validatePartTypes(parts)
