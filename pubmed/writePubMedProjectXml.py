#!/usr/bin/env python

import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.project as imp
import intermine.utils as imu
import synbio.dataset as sbds

############
### MAIN ###
############
parser = imu.ArgParser('Add PubMed source entry to InterMine SynBioMine project XML.')
parser.add_argument('datasetPath', help='path to the dataset location.')
parser.add_argument('pubMedDataPath', help='path to gene2pubmed file.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

datasetPath = args.datasetPath
ds = sbds.Dataset(datasetPath)
pubMedDataPath = args.pubMedDataPath

logPath = "%s/logs/writeOrthoDbProjectXml.log" % datasetPath
sys.stdout = imu.Logger(logPath)
projectXmlPath = "%s/intermine/project.xml" % datasetPath

imp.addSourcesToProject(
    "%s/intermine/project.xml" % datasetPath,
    [
        imp.Source(
            'pubmed-gene', 'pubmed-gene',
            [
                { 'name':'src.data.dir',            'location':os.path.dirname(pubMedDataPath) },
                { 'name':'src.data.dir.includes',   'value':'gene2pubmed' },
                { 'name':'pubmed.organisms',        'value':ds.getTaxonsAsString() }
            ]),

        imp.Source(
            'update-publications', 'update-publications',
            [
                { 'name':'src.data.file', 'location':'build/publications.xml' },
                { 'name':'loadFullRecord', 'value':'true' }
            ])
    ])