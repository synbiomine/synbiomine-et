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
    return _getUniprotData(ds, 'sprot', 'yes', taxon)

def getTremblData(ds, taxon):
    return _getUniprotData(ds, 'trembl', 'no', taxon)

def _getUniprotData(ds, databaseName, reviewed, taxon):
    """
    :param ds:
    :param databaseName: 'uniprot' or 'sprot'
    :param reviewed: 'yes' for sprot, 'no' for uniprot
    :param taxon:
    :return:
    """

    # compress=yes makes this take vastly longer
    uriStub = 'http://www.uniprot.org/uniprot/?query=organism:%s+reviewed:%s&include=yes' % (taxon, reviewed)
    resp = requests.get(uriStub + '&format=list')
    results = int(resp.headers['X-Total-Results'])
    print('Got %d %s results' % (results, databaseName))

    if results > 0:
        localPath = '%s/%s_uniprot_%s.xml' % (ds.getLoadPath(), taxon, databaseName)

        while True:
            # reviewed:yes (sprot) proteomes are human curated
            resp = requests.get(uriStub + '&format=xml')

            with open(localPath, 'w') as f:
                f.write(resp.text)

            if os.path.getsize(localPath) > 0:
                break
            else:
                print('Retrying download of %s since size is unexpectedly 0' % localPath)

    return results

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
    getTremblData(ds, taxon)
