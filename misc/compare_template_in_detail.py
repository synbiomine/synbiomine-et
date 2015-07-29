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

# Very crude comparison
print '### RESULTS FOUND IN SERVICE A ONLY ###'
for strA in strsA:
  if strA not in strsB:
    print strA
    countInBOnly += 1

print '### RESULTS FOUND IN SERVICE B ONLY ###'
for strB in strsB:
  if strB not in strsA:
    print strB
    countInAOnly += 1

print "Results found in service A only: %d" % countInAOnly
print "Results found in service B only: %d" % countInBOnly
