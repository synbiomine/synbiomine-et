#!/usr/bin/env python3

import jargparse
import os
import requests
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def getSwissProtData(ds, taxon):
    uriStub = 'http://www.uniprot.org/uniprot/?query=organism:%s+reviewed:yes&include=yes' % taxon
    resp = requests.get(uriStub + 'format=list')
    results = int(resp.headers['X-Total-Results'])
    print('Got %s swiss-prot results' % results)

    if results > 0:
        sprotLocalPath = '%s/%s_uniprot_sprot.xml' % (ds.getLoadPath(), taxon)

        # reviewed:yes (sprot) proteomes are human curated
        resp = requests.get(uriStub + 'format=xml')

        with open(sprotLocalPath, 'w') as f:
            f.write(resp.text)

############
### MAIN ###
############
parser = jargparse.ArgParser('Fetch Uniprot XML for direct parsing by InterMine.')
parser.add_argument('colPath', help='path to the dataset collection.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('uniprot')
ds.startLogging(__file__)

taxons = dc.getTaxons()

print('Fetching %d taxons' % len(taxons))

for taxon in taxons:
    print('### Processing taxon: %s ###' % taxon)

    getSwissProtData(ds, taxon)

    resp = requests.get('http://www.uniprot.org/uniprot/?query=organism:%s+reviewed:no&format=list&include=yes' % (taxon))
    results = int(resp.headers['X-Total-Results'])
    print('Got %s trembl results' % results)

    if results > 0:
        tremblLocalPath = '%s/%s_uniprot_trembl.xml' % (ds.getLoadPath(), taxon)

        # reviewed:no (trembl) proteomes are machine curated
        resp = requests.get('http://www.uniprot.org/uniprot/?query=organism:%s+reviewed:no&format=xml&include=yes' % (taxon))

        with open(tremblLocalPath, 'w') as f:
            f.write(resp.text)