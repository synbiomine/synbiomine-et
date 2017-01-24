#!/usr/bin/env python3

import jargparse
import shutil
import subprocess

#################
### FUNCTIONS ###
#################
def writeProjectXml(path, colPath):
    print('Executing ' + path)
    subprocess.call([path, colPath])

############
### MAIN ###
############
parser = jargparse.ArgParser('Create the InterMine project XML for this data collection.')
parser.add_argument('colPath', help='path to the data collection')

args = parser.parse_args()
colPath = args.colPath

shutil.copy('config/project.xml.template', colPath + '/intermine/project.xml')
writeProjectXml('./infra/writeSynbioMineProjectXml.pl', colPath)
writeProjectXml('./sources/ecocyc/writeEcocycProjectXml.py', colPath)
writeProjectXml('./sources/uniprot/writeUniprotProjectXml.py', colPath)
writeProjectXml('./sources/eggnog/writeEggNogProjectXml.py', colPath)
writeProjectXml('./sources/promoters/writePromotersProjectXml.py', colPath)
writeProjectXml('./sources/geo/writeGeoProjectXml.py', colPath)
writeProjectXml('./sources/interpro/writeInterProProjectXml.py', colPath)
writeProjectXml('./sources/go/writeGoProjectXml.py', colPath)
writeProjectXml('./sources/goa/writeGoaProjectXml.py', colPath)
writeProjectXml('./sources/biogrid/writeBiogridProjectXml.py', colPath)
writeProjectXml('./sources/reactome/writeReactomeProjectXml.py', colPath)
writeProjectXml('./sources/orthodb/writeOrthoDbProjectXml.py', colPath)
writeProjectXml('./sources/path2model/writePath2ModelProjectXml.py', colPath)
writeProjectXml('./sources/parts/synbis/writeSynbisProjectXml.py', colPath)
writeProjectXml('./sources/pubmed/writePubMedProjectXml.py', colPath)
writeProjectXml('./sources/entrez/writeEntrezOrganismProjectXml.py', colPath)

