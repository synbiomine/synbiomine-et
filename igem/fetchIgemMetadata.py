#!/usr/bin/python

# requires
#   pip install beautifulsoup4 html5lib
# 
# This script exists to scrape out lists of IGEM parts from their web pages
# At the moment, only doing transcription regulators as a test
# http://parts.igem.org/Protein_coding_sequences/Transcriptional_regulators
#
# We need to do it this way because there's no API way to get a list of parts atm
# And the data dumps they provide are too old (newest from 2010)
#
# Of course, this is a horribly fragile way to do it, so an IGEM API to do this would be vastly better

import argparse
import httplib
import texttable
from bs4 import BeautifulSoup

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

host = "parts.igem.org"
url = "/Protein_coding_sequences/Transcriptional_regulators"

############
### MAIN ###
############
parser = MyParser('Scrape iGEM part metadata.')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

conn = httplib.HTTPConnection(host)

print "Fetching http://%s%s" % (host, url)
conn.request("GET", url)
resp = conn.getresponse()

# We have to use html5lib here because the iGEM pages are malformed (e.g. all <tr>s inside the last <th> tag because it wasn't closed - something a browser corrects automatically
soup = BeautifulSoup(resp.read(), 'html5lib')
conn.close()

# Multiple tables with this id on a page
tables = soup.find_all('table', id='assembly_plasmid_table')

summaryTable = texttable.Texttable()
summaryTable.add_row(['Part', 'Protein', 'Uniprot', 'Description'])

for table in tables:
  # print '### TABLE ###'

  for row in table.tbody.find_all('tr')[1:-1]:
    cols = row.find_all('td')

    if args.verbose:
      print 'Processing row',

    partName = cols[0].a.contents[0].strip()

    if args.verbose:
      print partName

    proteinName = cols[1].contents[0].strip()
    description = cols[2].contents[0].strip()
    uniprotName = cols[5].contents[0].strip()

    # We need to strip out uniccode for texttable - might need to loko for another module
    summaryTable.add_row([partName.encode('ascii', 'ignore'), proteinName.encode('ascii', 'ignore'), uniprotName.encode('ascii', 'ignore'), description.encode('ascii', 'ignore')])

print summaryTable.draw()
