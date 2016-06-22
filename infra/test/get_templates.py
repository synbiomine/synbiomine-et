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
templates = service.templates
for name in sorted(templates.keys()):
  print name

  template = service.get_template(name)
  params = template.to_query_params()

  for paramName in sorted(params.keys()):
    if paramName != 'name':
      print "  %s:%s" % (paramName, params[paramName])

  print
