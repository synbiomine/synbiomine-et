"""
Common code for manipulating the VPR data that has been downloaded for InterMine
"""

import glob
import os
import sys
import xmltodict

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.utils as imu

def loadPartsFromXml(ds):
    """
    Given a dataset, load all the POLEN parts xml to dicts

    Returns a dictionary <part-name>:<part>
    """

    imu.printSection('Loading VPR parts')

    parts = {}

    rawPartsXmlPaths = glob.glob("%s/parts/*.xml" % ds.getRawPath())
    for rawPartXmlPath in rawPartsXmlPaths:
        with open(rawPartXmlPath) as f:
            partE = xmltodict.parse(f, force_list=('Property',)).itervalues().next()

        name = partE['Name']

        if name in parts:
            print "When processing %s already found part with name %s" % (rawPartXmlPath, name)
        else:
            parts[name] = partE

    return parts