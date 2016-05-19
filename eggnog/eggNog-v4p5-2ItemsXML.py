#!/usr/bin/env python

import argparse
import gzip
import os
import re
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
    print '~~~ %s ~~~' % text

def addDataSetItem(doc, name, dataSourceItem):
    item = doc.createItem('DataSet')
    item.addAttribute('name', name)
    item.addAttribute('dataSource', dataSourceItem)
    doc.addItem(item)
    return item

def addDataSourceItem(doc, name, url):
    item = doc.createItem('DataSource')
    item.addAttribute('name', name)
    item.addAttribute('url', url)
    doc.addItem(item)
    return item

def addFuncCatItem(doc, dataSetItem, category, classifier, description):
    item = doc.createItem('FunctionalCategory')
    item.addAttribute('dataSets', [ dataSetItem ])
    item.addAttribute('category', category)
    item.addAttribute('classifier', classifier)
    item.addAttribute('name', description)
    doc.addItem(item)
    return item

def addGroupDescriptionItem(doc, dataSetItem, id, description):
    item = doc.createItem('EggNogCategory')
    item.addAttribute('dataSets', [ dataSetItem ])
    item.addAttribute('primaryIdentifier', id)
    item.addAttribute('description', description)
    doc.addItem(item)
    return item

def addFuncCats(doc, dataSetItem, funcCatsPath):
    with open(funcCatsPath) as f:
        eggNogRaw = f.read()
        eggNogSections = eggNogRaw.split('\n\n')

    for section in eggNogSections:
        lines = section.splitlines()
        division = lines[0]
        # print "division=[%s]" % division

        for line in lines[1:]:
            line = line.strip()
            m = re.match("^\[(?P<letter>.{1})\] (?P<description>.*)$", line)
            # print "line=[%s,%s]" % (m.group('letter'), m.group('description'))
            addFuncCatItem(doc, dataSetItem, division, m.group('letter'), m.group('description'))

def addGroupDescriptions(doc, dataSetItem, annotationsPath):
    with gzip.open(annotationsPath) as f:
        for line in f:
            # print "line %d [%s]" % (i, line)
            taxonLevel, groupId, proteinCount, speciesCount, funcCat, funcDescription = line.strip().split('\t')
            addGroupDescriptionItem(doc, dataSetItem, groupId, funcDescription)
            # i += 1

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

eggNogAnnotationsPath = "%s/data/bactNOG/bactNOG.annotations.tsv.gz" % eggNogPath
eggNogFuncCatsPath = "%s/eggnog4.functional_categories.txt" % eggNogPath
eggNogMembersPath = "%s/data/bactNOG/bactNOG.members.tsv.gz" % eggNogPath

sys.stdout = Logger(logPath)

model = IM.Model(modelPath)
doc = IM.Document(model)

dataSourceItem = addDataSourceItem(doc, 'EggNOG: A database of orthologous groups and functional annotation', 'http://eggnog.eml.de')
groupDataSetItem = addDataSetItem(doc, 'EggNOG Non-supervised Orthologous Groups', dataSourceItem)
funcCatDataSetItem = addDataSetItem(doc, 'EggNOG Functional Categories', dataSourceItem)

addFuncCats(doc, funcCatDataSetItem, eggNogFuncCatsPath)
addGroupDescriptions(doc, groupDataSetItem, eggNogAnnotationsPath)

doc.write(itemsPath)

"""
logEyeCatcher("Processing protein member files")

with gzip.open(eggNogMembersPath) as f:
  for line in f:
    print line
"""