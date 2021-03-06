#!/usr/bin/env python

import gzip
import os
import re
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as IM
import intermyne.utils as imu
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def addDataSetItem(doc, name, dataSourceItem):
    if beVerbose:
        print "Adding DataSet %s" % name

    item = doc.createItem('DataSet')
    item.addAttribute('name', name)
    item.addAttribute('dataSource', dataSourceItem)
    doc.addItem(item)
    return item

def addDataSourceItem(doc, name, url):
    if beVerbose:
        print "Adding DataSource %s" % name

    item = doc.createItem('DataSource')
    item.addAttribute('name', name)
    item.addAttribute('url', url)
    doc.addItem(item)
    return item

def addFuncCatItem(doc, dataSetItem, category, classifier, description):
    if beVerbose:
        print "Adding FunctionalCategory %s, %s, %s" % (category, classifier, description)

    item = doc.createItem('FunctionalCategory')
    item.addAttribute('dataSets', [ dataSetItem ])
    item.addAttribute('category', category)
    item.addAttribute('classifier', classifier)
    item.addAttribute('name', description)
    doc.addItem(item)
    return item

def addGroupItem(doc, dataSetItem, id, funcCatItems, description):
    if beVerbose:
        print "Adding EggNogCategory %s" % id

    item = doc.createItem('EggNogCategory')
    item.addAttribute('dataSets', [ dataSetItem ])
    item.addAttribute('primaryIdentifier', id)
    item.addAttribute('functionalCategories', funcCatItems)
    item.addAttribute('description', description)
    doc.addItem(item)
    return item

def addOrganismItem(doc, taxonId):
    if beVerbose:
        print "Adding Organism taxon %s" % taxonId

    item = doc.createItem('Organism')
    item.addAttribute('taxonId', taxonId)
    doc.addItem(item)
    return item

def addGeneItem(doc, organismItem, geneId):
    if beVerbose:
        print "Adding Gene %s %s" % (organismItem.getAttribute('taxonId'), geneId)

    item = doc.createItem('Gene')
    item.addAttribute('primaryIdentifier', geneId)
    item.addAttribute('secondaryIdentifier', geneId)
    item.addAttribute('organism', organismItem)
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

    if beVerbose:
        print "Reading from %s" % funcCatsPath

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

    if beVerbose:
        print "Reading from %s" % annotationsPath

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

            groupItems[groupId] = addGroupItem(doc, dataSetItem, groupId, funcCatItemsForGroup, funcDescription)

            for funcCatItem in funcCatItemsForGroup:
                funcCatItem.addToAttribute('eggNogCategories', groupItems[groupId])

            # i += 1

    return groupItems

def addGeneItems(doc, groupItems, membersPath, taxons):

    if beVerbose:
        print "Reading from %s" % membersPath

    with gzip.open(membersPath) as f:
        geneItems = {}
        organismItems = {}

        for line in f:
            line = line.strip()
            taxLevel, groupId, proteinCount, speciesCount, funcCat, eggNogGeneIds = line.split('\t')

            for eggNogGeneId in eggNogGeneIds.split(','):
                taxonId, geneId = eggNogGeneId.split('.', 1)

                # We must filter out taxons that we are not directly loading into Synbiomine.  Otherwise we get 1.3 GB
                # of items that cannot even be loaded by InterMine at the moment.  This is the same as the behaviour of
                # the previous Perl script for processing EggNOG 4.0
                if taxonId not in taxons:
                    continue

                if taxonId not in organismItems:
                    organismItems[taxonId] = addOrganismItem(doc, taxonId)

                if geneId not in geneItems:
                    geneItems[geneId] = addGeneItem(doc, organismItems[taxonId], geneId)

                geneItem = geneItems[geneId]
                groupItem = groupItems[groupId]

                geneItem.addToAttribute('eggNogCategories', groupItem)
                groupItem.addToAttribute('genes', geneItem)

    return organismItems, geneItems

############
### MAIN ###
############
parser = imu.ArgParser('Take files from EggNOG and produce Functional Categories, EggNOG orthology groups and map bacterial genes to these.')
parser.add_argument('colPath', help='path to the data collection.')
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
args = parser.parse_args()

beVerbose = args.verbose

dc = sbd.Collection(args.colPath)
ds = dc.getSet('eggnog')
ds.startLogging(__file__)

rawPath = ds.getRawPath()
eggNogAnnotationsPath = "%s/data/bactNOG/bactNOG.annotations.tsv.gz" % rawPath
eggNogFuncCatsPath = "%s/eggnog4.functional_categories.txt" % rawPath
eggNogMembersPath = "%s/data/bactNOG/bactNOG.members.tsv.gz" % rawPath

model = dc.getModel()
doc = IM.Document(model)

imu.printSection("Adding data source and data set items")
dataSourceItem = addDataSourceItem(doc, 'EggNOG: A database of orthologous groups and functional annotation', 'http://eggnog.eml.de')
groupDataSetItem = addDataSetItem(doc, 'EggNOG Non-supervised Orthologous Groups', dataSourceItem)
funcCatDataSetItem = addDataSetItem(doc, 'EggNOG Functional Categories', dataSourceItem)

imu.printSection("Adding functional category items")
funcCatItems = addFuncCatItems(doc, funcCatDataSetItem, eggNogFuncCatsPath)
print "Added %d functional category items" % len(funcCatItems)

imu.printSection("Adding group description items")
groupItems = addGroupItems(doc, groupDataSetItem, funcCatItems, eggNogAnnotationsPath)
print "Added %d EggNOG group items" % len(groupItems)

imu.printSection("Adding gene and organism items")
organismItems, geneItems = addGeneItems(doc, groupItems, eggNogMembersPath, dc.getTaxons())
print "Added %d organism items" % len(organismItems)
print "Added %d gene items" % len(geneItems)

imu.printSection("Writing InterMine item XML")
doc.write(ds.getLoadPath() + '/items.xml')