#!/usr/bin/python

import argparse
import sys
from intermine.webservice import Service

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

###################
### SUBROUTINES ###
###################
def compareCrude(rowsA, rowsB, verbose):
  strsA = map(str, rowsA)
  strsB = map(str, rowsB)

  countInAOnly = 0
  countInBOnly = 0
  countInBoth = 0

  """
  for rowA in rowsA:
    if rowA['Gene.symbol'] == 'acoR':
      print rowA

  for rowB in rowsB:
    if rowB['Gene.symbol'] == 'acoR':
      print rowB
  """

  # Very crude comparison
  print '#######################################'
  print '### RESULTS FOUND IN SERVICE A ONLY ###'
  print '#######################################'

  for strA in strsA:
    if strA not in strsB:
      print strA
      countInAOnly += 1
    else:
      countInBoth += 1

  print '#######################################'
  print '### RESULTS FOUND IN SERVICE B ONLY ###'
  print '#######################################'

  for strB in strsB:
    if strB not in strsA:
      print strB
      countInBOnly += 1

  print "Results found in service A only: %d" % countInAOnly
  print "Results found in service B only: %d" % countInBOnly
  print "Results found in both: %d" % countInBoth

def indexItemsByKey(rows, keyName, verbose):
  items = {}
  itemsErrorCount = 0
  for row in rows:
    key = row[keyName]

    if key in items:
      itemsErrorCount += 1
      if verbose:
        print "ERROR %d\n%s\nalready found as\n%s\n" % (itemsErrorCount, str(row), str(items[key]))
    else:
      items[key] = row

  print "Removed %d of %d as duplicated items" % (len(rows) - len(items), len(rows))

  return items

def compareWithKey(rowsA, rowsB, keyName, verbose):
#  print len(rowsA)
#  print len(rowsB)

  print "Analyzing service A items"
  itemsA = indexItemsByKey(rowsA, keyName, verbose)

  print "Analyzing service B items"
  itemsB = indexItemsByKey(rowsB, keyName, verbose)
  print 

  countInAOnly = 0
  countInBOnly = 0
  countInBoth = 0

  print '#######################################'
  print '### RESULTS FOUND IN SERVICE A ONLY ###'
  print '#######################################'

  for keyA in itemsA.keys():
    if keyA not in itemsB:
      # if verbose:
      print str(itemsA[keyA])
      countInAOnly += 1
    else:
      countInBoth += 1
  
  print '#######################################'
  print '### RESULTS FOUND IN SERVICE B ONLY ###'
  print '#######################################'

  for keyB in itemsB.keys():
    if keyB not in itemsA:
      # if verbose:
      print str(itemsB[keyB])
      countInBOnly += 1

  print "Results found in service A only: %d" % countInAOnly
  print "Results found in service B only: %d" % countInBOnly
  print "Results found in both: %d" % countInBoth

############
### MAIN ###
############
parser = MyParser('Compare a template between two versions of the same webservice in detail.')
parser.add_argument('-v', '--verbose')
parser.add_argument('-k', '--key')
parser.add_argument('template_name')
parser.add_argument('service_version_a')
parser.add_argument('service_version_b')
args = parser.parse_args()

serviceA = Service(args.service_version_a)
templateA = serviceA.get_template(args.template_name)
rowsA = templateA.get_row_list()

serviceB = Service(args.service_version_b)
templateB = serviceB.get_template(args.template_name)
rowsB = templateB.get_row_list()

if args.key:
  compareWithKey(rowsA, rowsB, args.key, args.verbose)
else:
  compareCrude(rowsA, rowsB, args.verbose)
