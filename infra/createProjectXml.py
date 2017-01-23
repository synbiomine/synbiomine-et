#!/usr/bin/env python3

import jargparse
import shutil
import subprocess

#################
### FUNCTIONS ###
#################
def writeProjectXml(path):
    print('Executing ' + path)
    subprocess.call([path, colPath])

############
### MAIN ###
############
parser = jargparse.ArgParser('Create the InterMine project XML for this data collection.')
parser.add_argument('colPath', help='path to the data collection')

args = parser.parse_args()

colPath = args.colPath

shutil.copy('etc/project.xml.template', colPath + '/intermine/project.xml')
writeProjectXml('./infra/writeSynbioMineProjectXml.pl')
writeProjectXml('./sources/ecocyc/writeEcocycProjectXml.py')
writeProjectXml('./sources/uniprot/writeUniprotProjectXml.py')
writeProjectXml('./sources/eggnog/writeEggNogProjectXml.py')
writeProjectXml('./sources/promoters/writePromotersProjectXml.py')
writeProjectXml('./sources/geo/writeGeoProjectXml.py')
writeProjectXml('./sources/interpro/writeInterProProjectXml.py')
writeProjectXml('./sources/go/writeGoProjectXml.py')
writeProjectXml('./sources/goa/writeGoaProjectXml.py')
writeProjectXml('./sources/biogrid/writeBiogridProjectXml.py')
writeProjectXml('./sources/reactome/writeReactomeProjectXml.py')
writeProjectXml('./sources/orthodb/writeOrthoDbProjectXml.py')
writeProjectXml('./sources/path2model/writePath2ModelProjectXml.py')
writeProjectXml('./sources/parts/synbis/writeSynbisProjectXml.py')
writeProjectXml('./sources/pubmed/writePubMedProjectXml.py')
writeProjectXml('./sources/entrez/writeEntrezOrganismProjectXml.py')
