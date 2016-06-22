#!/usr/bin/python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
from intermine.webservice import Service
import intermyne.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Get results from executing a given template on a given service')
parser.add_argument('template')
parser.add_argument('service')
args = parser.parse_args()

serviceA = Service(args.service)
templateA = serviceA.get_template(args.template)
rowsA = templateA.get_row_list()
strsA = map(str, rowsA)

for strA in strsA:
    print strA
