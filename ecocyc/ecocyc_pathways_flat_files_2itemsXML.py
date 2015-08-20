#!/usr/bin/python

import argparse
import os
import os.path
import sys
import urllib

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

############
### MAIN ###
############
parser = MyParser('Tranform ecocyc pathways flat files to InterMine items import xml.')
parser.add_argument('inputPath', help='the directory containing the input flat files.')
args = parser.parse_args()

pathwaysDatFn = "pathways.dat"

if not os.path.isdir(args.inputPath):
  print >> sys.stderr, "Path [%s] is not a directory" % args.inputPath
  sys.exit(1)

inputPath = args.inputPath
pathways = {}

with open("%s/%s" % (inputPath, pathwaysDatFn)) as f:
  # Used to add continued lines
  lastKey = None

  pathway = None

  for line in f:
    line = line.strip(os.linesep)
    line = urllib.unquote(line)

    # Ignore comments
    if line.startswith('#'):
      continue

    # Terminate record
    if line == '//':
      if pathway == None:
        print >> sys.stderr, "Found record end with no associated pathway."
        sys.exit(1)
      else:
        # print "Ending record for pathway %s" % pathway['UNIQUE-ID'][0]

        pathways[pathway['UNIQUE-ID'][0]] = pathway
        pathway = None
        lastKey = None
        continue

    # Process continued line
    if line.startswith('/'):
      if pathway == None:
        print >> sys.stderr, "Found continued line but with no current pathway."
        sys.exit(1)
      if lastKey == None:
        print >> sys.stderr, "Found continued line for pathway %s but with no last key." % pathway['UNIQUE-ID']
        sys.exit(1)
      else:
        pathway[lastKey][-1] += value
        continue

    # Complain if we now have a line not containing '-'
    # All such valid lines would be dealt with by the logic above
    if not '-' in line:
      print >> sys.stderr, "Did not find '-' in line [%s]" % line
      sys.exit(1)

    (key, value) = line.split(' - ', 1)
    # print "%s:%s" % (key, value)

    # Setup new pathway record
    if key == 'UNIQUE-ID':
      # Sanity
      if pathway != None:
        print >> sys.stderr, "Found new UNIQUE-ID %s but still have unfinished pathway %s" % (value, pathway['UNIQUE-ID'])
        sys.exit(1)

      print "Processing pathway %s" % value

      pathway = {}

    # Add value to key entry
    if not key in pathway:
      pathway[key] = []

    pathway[key].append(value)

    lastKey = key

if pathway != None:
  print >> sys.stderr, "Finished processing %s but still in unclosed pathway %s" % (pathwaysDatFn, pathway['UNIQUE-ID'])
  sys.exit(1)

print "Processed %d pathways" % len(pathways)
