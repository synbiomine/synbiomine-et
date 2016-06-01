#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Add PubMed source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('pubMedDataPath', help='path to gene2pubmed file.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
pubMedDataPath = args.pubMedDataPath

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath
taxonsPath = "%s/taxons/taxons.txt" % datasetPath

with open(taxonsPath) as f:
    taxons = f.read().strip()

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
        'pubmed-gene', 'pubmed-gene',
        [
            { 'name':'src.data.dir',            'location':os.path.dirname(pubMedDataPath) },
            { 'name':'src.data.dir.includes',   'value':os.path.basename(pubMedDataPath) },
            { 'name':'pubmed.organisms',        'value':taxons }
        ],
        dump=True)
    ])