#!/usr/bin/env python3

import jargparse
import shutil
import subprocess

parser = jargparse.ArgParser('Create the InterMine project XML for this data collection.')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

colPath = args.colPath

shutil.copy('etc/project.xml.template', colPath + '/intermine/project.xml')
subprocess.call(['./infra/writeSynbioMineProjectXml.pl', colPath])
