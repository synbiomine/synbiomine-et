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
parser = MyParser('Compare a template between two versions of the same webservice in detail.')
parser.add_argument('template_name')
parser.add_argument('service_version_a')
parser.add_argument('service_version_b')
args = parser.parse_args()

serviceA = Service(args.service_version_a)
templateA = serviceA.get_template(args.template_name)

"""
for c in templateA.editable_constraints:
  print c
"""

rowsA = templateA.get_row_list()
strsA = map(str, rowsA)

serviceB = Service(args.service_version_b)
templateB = serviceB.get_template(args.template_name)
rowsB = templateB.get_row_list()
strsB = map(str, rowsB)

countInAOnly = 0
countInBOnly = 0

"""
for rowA in rowsA:
  if rowA['Gene.symbol'] == 'acoR':
    print rowA

for rowB in rowsB:
  if rowB['Gene.symbol'] == 'acoR':
    print rowB
"""

# Very crude comparion
for strA in strsA:
  print strA
  if strA in strsB:
    countInBOnly += 1

for strB in strsB:
  if strB not in strsA:
    countInAOnly += 1

print "Results found in A only: %d" % countInAOnly
print "Results found in B only: %d" % countInBOnly
