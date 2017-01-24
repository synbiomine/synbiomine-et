#!/usr/bin/env python3

import jargparse
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.project as imp
import synbio.data as sbd

############
### MAIN ###
############
parser = jargparse.ArgParser('Add Uniprot source entries to InterMine SynBioMine project XML.')
parser.add_argument('colPath', help='path to the dataset collection.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('uniprot')
ds.startLogging(__file__)

uniprotDataPath = '{{imDataPath}}/uniprot'

imp.addSourcesToProject(
    dc.getProjectXmlPath(),
    [
        imp.Source('uniprot', 'uniprot',
        [
            { 'name':'src.data.dir',        'location':uniprotDataPath },
            { 'name':'uniprot.organisms',   'value':dc.getTaxonsAsString() }
        ],
        dump=True),

        imp.Source(
            'uniprot-fasta', 'fasta',
            [
                { 'name':'src.data.dir',            'location':uniprotDataPath },
                { 'name':'fasta.taxonId',           'value':dc.getTaxonsAsString() },
                { 'name':'fasta.className',         'value':'org.intermine.model.bio.Protein' },
                { 'name':'fasta.classAttribute',    'value':'primaryAccession' },
                { 'name':'fasta.dataSetTitle',      'value':'UniProt data set' },
                { 'name':'fasta.dataSourceName',    'value':'UniProt' },
                { 'name':'fasta.includes',          'value':'uniprot_sprot_varsplic.fasta' },
                { 'name':'fasta.sequenceType',      'value':'protein' },
                { 'name':'fasta.loaderClassName',   'value':'org.intermine.bio.dataconversion.UniProtFastaLoaderTask' }
            ],
        dump=True),

        imp.Source(
            'uniprot-keywords', 'uniprot-keywords',
            [
                { 'name':'src.data.dir',            'location':uniprotDataPath },
                { 'name':'src.data.dir.includes',   'value':'keywlist.xml' }
            ],
        dump=True)
    ])