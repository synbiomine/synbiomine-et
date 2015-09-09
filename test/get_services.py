#!/usr/bin/python

import argparse
import json
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
parser = MyParser('Show information on all services available from the mine.')
parser.add_argument('mineURL', help = "mine URL.  For example, http://synbiomine.org/synbiomine")
args = parser.parse_args()

f = urllib.urlopen("%s/service" % args.mineURL)
o = json.load(f)
print json.dumps(o, indent=4)
