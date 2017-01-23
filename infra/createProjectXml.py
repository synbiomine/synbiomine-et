#!/usr/bin/env python3

import jargparse
import shutil
import subprocess

parser = jargparse.ArgParser('Create the InterMine project XML for this data collection.')
parser.add_argument('colPath', help='path to the data collection')

args = parser.parse_args()

colPath = args.colPath

shutil.copy('etc/project.xml.template', colPath + '/intermine/project.xml')
subprocess.call(['./infra/writeSynbioMineProjectXml.pl',                colPath])
subprocess.call(['./sources/ecocyc/writeEcocycProjectXml.py',           colPath])
subprocess.call(['./sources/uniprot/writeUniprotProjectXml.py',         colPath])
subprocess.call(['./sources/eggnog/writeEggNogProjectXml.py',           colPath])
subprocess.call(['./sources/promoters/writePromotersProjectXml.py',     colPath])
subprocess.call(['./sources/geo/writeGeoProjectXml.py',                 colPath])
subprocess.call(['./sources/interpro/writeInterProProjectXml.py',       colPath])
subprocess.call(['./sources/go/writeGoProjectXml.py',                   colPath])
subprocess.call(['./sources/goa/writeGoaProjectXml.py',                 colPath])
subprocess.call(['./sources/biogrid/writeBiogridProjectXml.py',         colPath])
subprocess.call(['./sources/reactome/writeReactomeProjectXml.py',       colPath])
subprocess.call(['./sources/orthodb/writeOrthoDbProjectXml.py',         colPath])
subprocess.call(['./sources/path2model/writePath2ModelProjectXml.py',   colPath])
subprocess.call(['./sources/parts/synbis/writeSynbisProjectXml.py',     colPath])
subprocess.call(['./sources/pubmed/writePubMedProjectXml.py',           colPath])
subprocess.call(['./sources/entrez/writeEntrezOrganismProjectXml.py',   colPath])
