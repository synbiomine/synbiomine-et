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
parser = MyParser(
  'Run an arbitrary xml query on a service.', 
  formatter_class=argparse.RawDescriptionHelpFormatter,
  epilog='''QUERY EXAMPLE:
<query view="Gene.primaryIdentifier Gene.symbol" sortOrder="Gene.primaryIdentifier asc">
  <constraint path="Gene.organism.name" code="A" editable="true" op="=" value="Escherichia coli str. K-12 substr. MG1655"/>
</query>''')
parser.add_argument('query', help='query XML')
parser.add_argument('service', help='InterMine service URL.  e.g. http://synbiomine.org/synbiomine')
args = parser.parse_args()

service = Service(args.service)
query = Query.from_xml(args.query, service.model)
query.service = service

for row in query.rows():
  print row

print
print "Rows: %d" % query.count()
