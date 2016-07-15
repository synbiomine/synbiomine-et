#!/usr/bin/python

import argparse
import sys
import urllib

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser(
  'Run a GFF3 query on InterMine.',
  formatter_class=argparse.RawDescriptionHelpFormatter,
  epilog='''QUERY EXAMPLE:
<query view="Gene.primaryIdentifier Gene.symbol" sortOrder="Gene.primaryIdentifier asc">
  <constraint path="Gene.organism.name" code="A" editable="true" op="=" value="Escherichia coli str. K-12 substr. MG1655"/>
</query>''')
parser.add_argument('query', help='query XML')
parser.add_argument('serviceURL', help='InterMine service URL.  e.g. http://synbiomine.org/synbiomine')
args = parser.parse_args()

f = urllib.urlopen("%s/service/query/results/gff3" % args.serviceURL)
d = f.read()
print f
