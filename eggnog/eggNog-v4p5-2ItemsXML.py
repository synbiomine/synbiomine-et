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

def addGroupDescriptionItem(doc, dataSetItem, id, funcCatItems, description):
    item = doc.createItem('EggNogCategory')
    item.addAttribute('dataSets', [ dataSetItem ])
    item.addAttribute('primaryIdentifier', id)
    item.addAttribute('functionalCategories', funcCatItems)
    item.addAttribute('description', description)
    doc.addItem(item)
    return item

def addFuncCatItems(doc, dataSetItem, funcCatsPath):
    """
    Add functional category items to the document.

    :param doc:
    :param dataSetItem:
    :param funcCatsPath:
    :return: dictionary where letter => item
    """

    with open(funcCatsPath) as f:
        eggNogRaw = f.read()
        eggNogSections = eggNogRaw.split('\n\n')

    funcCatItems = {}

    for section in eggNogSections:
        lines = section.splitlines()
        division = lines[0]
        # print "division=[%s]" % division

        for line in lines[1:]:
            line = line.strip()
            m = re.match("^\[(?P<letter>.{1})\] (?P<description>.*)$", line)
            # print "line=[%s,%s]" % (m.group('letter'), m.group('description'))
            letter, description = m.group('letter'), m.group('description')
            item = addFuncCatItem(doc, dataSetItem, division, letter, description)
            funcCatItems[letter] = item

    return funcCatItems

def addGroupItems(doc, dataSetItem, funcCatItems, annotationsPath):
    """
    Add group items to the document.  Also adds those group item references to the functional category item.

    :return: dictionary where group-id => item
    """

    with gzip.open(annotationsPath) as f:
        groupItems = {}

        for line in f:
            line = line.strip()
            # print "line [%s]" % (line)
            taxonLevel, groupId, proteinCount, speciesCount, funcCatIds, funcDescription = line.split('\t')

            # The functional categories column will have multiple letter for multiple categories (e.g. 'DZ')
            funcCatItemsForGroup = []
            for funcCatId in funcCatIds:
                funcCatItemsForGroup.append(funcCatItems[funcCatId])

            groupItems[groupId] = addGroupDescriptionItem(doc, dataSetItem, groupId, funcCatItemsForGroup, funcDescription)

            for funcCatItem in funcCatItemsForGroup:
                funcCatItem.addToAttribute('eggNogCategories', groupItems[groupId])

            # i += 1

    return groupItems

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

logEyeCatcher("Adding data source and data set items")
dataSourceItem = addDataSourceItem(doc, 'EggNOG: A database of orthologous groups and functional annotation', 'http://eggnog.eml.de')
groupDataSetItem = addDataSetItem(doc, 'EggNOG Non-supervised Orthologous Groups', dataSourceItem)
funcCatDataSetItem = addDataSetItem(doc, 'EggNOG Functional Categories', dataSourceItem)

logEyeCatcher("Adding functional category items")
funcCatItems = addFuncCatItems(doc, funcCatDataSetItem, eggNogFuncCatsPath)

logEyeCatcher("Adding group description items")
groupItems = addGroupItems(doc, groupDataSetItem, funcCatItems, eggNogAnnotationsPath)

doc.write(itemsPath)

"""
logEyeCatcher("Processing protein member files")

with gzip.open(eggNogMembersPath) as f:
  for line in f:
    print line
"""