#!/usr/bin/python

import argparse
import sys
from intermine.webservice import Service

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser('Get results from executing a given template on a given service')
parser.add_argument('template')
parser.add_argument('service')
args = parser.parse_args()

serviceA = Service(args.service)
templateA = serviceA.get_template(args.template)
rowsA = templateA.get_row_list()
strsA = map(str, rowsA)

for strA in strsA:
  print strA
