#!/usr/bin/env python

import os
import sys
import shutil

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add OrthoDB source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
uniprotDataPath = 'uniprot'

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath
taxonsPath = "%s/taxons/taxons.txt" % datasetPath

with open(taxonsPath) as f:
    taxons = f.read().strip()

project = imp.Project("%s/intermine/project.xml" % datasetPath)

source = imp.Source(
    'uniprot', 'uniprot',
    [
        { 'name':'src.data.dir',        'location':uniprotDataPath },
        { 'name':'uniprot.organisms',   'value':taxons }
    ],
    dump=True)
project.addSource(source)

source = imp.Source(
    'uniprot-fasta', 'fasta',
    [
        { 'name':'src.data.dir',            'location':uniprotDataPath },
        { 'name':'fasta.taxonId',           'value':taxons },
        { 'name':'fasta.className',         'value':'org.intermine.model.bio.Protein' },
        { 'name':'fasta.classAttribute',    'value':'primaryAccession' },
        { 'name':'fasta.dataSetTitle',      'value':'UniProt data set' },
        { 'name':'fasta.dataSourceName',    'value':'UniProt' },
        { 'name':'fasta.includes',          'value':'uniprot_sprot_varsplic.fasta' },
        { 'name':'fasta.sequenceType',      'value':'protein' },
        { 'name':'fasta.loaderClassName',   'value':'org.intermine.bio.dataconversion.UniProtFastaLoaderTask' }
    ],
    dump=True)
project.addSource(source)

source = imp.Source(
    'uniprot-keywords', 'uniprot-keywords',
    [
        { 'name':'src.data.dir',            'location':uniprotDataPath },
        { 'name':'src.data.dir.includes',   'value':'keywlist.xml' }
    ],
    dump=True)
project.addSource(source)

shutil.copy(projectXmlPath, "%s.bak" % projectXmlPath)
project.write(projectXmlPath)