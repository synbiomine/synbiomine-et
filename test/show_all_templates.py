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
parser = MyParser('Show information on all templates available from a service')
parser.add_argument('service', help = "service URL")
args = parser.parse_args()

service = Service(args.service)
for name in service.templates.keys():
  print name
