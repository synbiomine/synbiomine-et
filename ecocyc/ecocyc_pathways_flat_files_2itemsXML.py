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

###################
### SUBROUTINES ###
###################

############
### MAIN ###
############
parser = MyParser('Tranform ecocyc pathways flat files to InterMine items import xml.')
parser.add_argument('inputPath', help='the directory containing the input flat files.')
args = parser.parse_args()

if not os.path.isdir(args.inputPath):
  print >> sys.stderr, "Path [%s] is not a directory" % args.inputPath
  sys.exit(1)

inputPath = args.inputPath
pathways = {}

with open("%s/pathways.dat" % inputPath) as f:
  pathway = None

  for line in f:
    line = line.strip(os.linesep)

    if line.startswith('#'):
      continue

    # print "[%s]" % line

    if line == '//':
      if pathway == None:
        print >> sys.stderr, "Found record end with no associated pathway."
        sys.exit(1)
      
      print "Ending record for pathway %s" % pathway['UNIQUE-ID'][0]

      pathways[pathway['UNIQUE-ID'][0]] = pathway
      pathway = None
      continue

    # Skip temporarily
    if not '-' in line:
      continue

    # Skip temporarily
    if line.startswith('/'):
      continue

    (key, value) = line.split(' - ', 1)
    value = urllib.unquote(value)
    # print "%s:%s" % (key, value)

    if key == 'UNIQUE-ID':
      # Sanity
      if pathway != None:
        print >> sys.stderr, "Found new UNIQUE-ID %s but still have unfinished pathway %s" % (value, pathway['UNIQUE-ID'])
        sys.exit(1)

      print "Processing pathway %s" % value

      pathway = {}

    if not key in pathway:
      pathway[key] = []

    pathway[key].append(value)

print "Processed %d pathways" % len(pathways)
