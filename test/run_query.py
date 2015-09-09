#!/usr/bin/python

import argparse
import sys
from intermine.webservice import Query, Service

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser('Run an arbitrary xml query on a service.')
parser.add_argument('query')
parser.add_argument('service')
args = parser.parse_args()

service = Service(args.service)
query = Query.from_xml(args.query, service.model)
query.service = service

for row in query.rows():
  print row

print
print "Rows: %d" % query.count()
