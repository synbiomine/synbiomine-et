#!/usr/bin/env python

import argparse
import gzip
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermine.model as IM

class Logger(object):
    def __init__(self, logPath):
        self.terminal = sys.stdout
        self.log = open(logPath, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

#################
### FUNCTIONS ###
#################
def logEyeCatcher(text):
    print "~~~ %s ~~~" % text

def addDataSetItem(doc, dsItem):
    item = doc.createItem("DataSet")
    item.addAttribute('name', 'EggNOG Non-supervised Orthologous Groups')
    item.addAttribute('dataSource', dsItem)
    doc.addItem(item)
    return item

def addDataSourceItem(doc, name, url):
    item = doc.createItem("DataSource")
    item.addAttribute('name', name)
    item.addAttribute('url', url)
    doc.addItem(item)
    return item

############
### MAIN ###
############
parser = MyParser('Take files from EggNOG and produce Functional Categories, EggNOG orthology groups and map bacterial genes to these.')
parser.add_argument('eggNogPath', help='previously fetched data files from eggNOG.')
parser.add_argument('datasetPath', help='path to the dataset.')
parser.add_argument('modelPath', help='path to the InterMine genomic model XML')
args = parser.parse_args()

eggNogPath = args.eggNogPath
datasetPath = args.datasetPath
modelPath = args.modelPath

itemsPath = "%s/eggnog/eggnog-items.xml" % datasetPath

logPath = "%s/logs/eggNog-v4p5-2ItemsXML.log" % datasetPath
eggNogMembersPath = "%s/data/bactNOG/bactNOG.members.tsv.gz" % eggNogPath

sys.stdout = Logger(logPath)

model = IM.Model(modelPath)
doc = IM.Document(model)

dsItem = addDataSourceItem(doc, 'EggNOG: A database of orthologous groups and functional annotation', 'http://eggnog.eml.de')
addDataSetItem(doc, dsItem)

doc.write(itemsPath)

"""
logEyeCatcher("Processing protein member files")

with gzip.open(eggNogMembersPath) as f:
  for line in f:
    print line
"""