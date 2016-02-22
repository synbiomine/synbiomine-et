#!/usr/bin/python

# Compare previously fetched database statistical information

import argparse
import json
import sys
import texttable

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

############
### MAIN ###
############
parser = MyParser('Compare previously fetched information about InterMine databases.')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('jsonFile', nargs='*')
args = parser.parse_args()

data = []
for fileName in args.jsonFile:
  if args.verbose:
    print "Loading %s" % (fileName)

  with open(fileName) as f:
    data.append(json.load(f))

# All keys across mines
allTableNames = set()
for mine in data:
  for table in mine['tables']:
    allTableNames.add(table)

prettySummaryTable = texttable.Texttable()

mineNames = []
for mine in data:
  mineNames.append(mine['name'])

prettySummaryTable.add_row(['Table Name'] + mineNames)

for tableName in sorted(allTableNames):
  row = [ tableName ]
  for mine in data:
    if tableName in mine['tables']:
      row.append('{:,}'.format(mine['tables'][tableName]))
    else:
      row.append('-')
  prettySummaryTable.add_row(row)

print prettySummaryTable.draw()
