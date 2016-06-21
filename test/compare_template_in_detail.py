#!/usr/bin/python

import os
import sys
from intermine.webservice import Service

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.utils as imu

###################
### SUBROUTINES ###
###################
def compareCrude(rowsA, rowsB, verbose):
  strsA = map(str, rowsA)
  strsB = map(str, rowsB)

  strsAOnly = []
  strsBOnly = []
  strsBoth = []

  for strA in strsA:
    if strA not in strsB:
      strsAOnly.append(strA)
    else:
      strsBoth.append(strA)

  for strB in strsB:
    if strB not in strsA:
      strsBOnly.append(strB)

  return {'strsAOnly':strsAOnly, 'strsBOnly':strsBOnly, 'strsBoth':strsBoth}

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

  print "Analyzing service A items"
  itemsA = indexItemsByKey(rowsA, keyName, verbose)

  print "Analyzing service B items"
  itemsB = indexItemsByKey(rowsB, keyName, verbose)
  print 

  strsAOnly = []
  strsBOnly = []
  strsBoth = []

  for keyA in itemsA.keys():
    if keyA not in itemsB:
      strsAOnly.append(itemsA[keyA])
    else:
      strsBOnly.append(itemsA[keyA])

  for keyB in itemsB.keys():
    if keyB not in itemsA:
      strsBOnly.append(strB)

  return {'strsAOnly':strsAOnly, 'strsBOnly':strsBOnly, 'strsBoth':strsBoth}

############
### MAIN ###
############
parser = imu.ArgParser('Compare a template between two versions of the same webservice in detail.')
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

results = None

if args.key:
  res = compareWithKey(rowsA, rowsB, args.key, args.verbose)
else:
  res = compareCrude(rowsA, rowsB, args.verbose)

print '#######################################'
print '### RESULTS FOUND IN SERVICE A ONLY ###'
print '#######################################'

for s in res['strsAOnly']:
  print s

print '#######################################'
print '### RESULTS FOUND IN SERVICE B ONLY ###'
print '#######################################'

for s in res['strsBOnly']:
  print s

print "Results found in service A only: %d" % len(res['strsAOnly'])
print "Results found in service B only: %d" % len(res['strsBOnly'])
print "Results found in both: %d" % len(res['strsBoth'])
