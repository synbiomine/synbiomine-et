#!/usr/bin/env python

import glob
import jargparse
import os
import sys
import xmltodict

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../../modules/python')
import intermyne.model as imm
import intermyne.utils as imu
import jbio.sources.go as go
import synbio.data as sbd

#################
### FUNCTIONS ###
#################
def loadInteractionsXml(ds):
    """
    Given a dataset, load all the POLEN interactions xml to dicts
    """

    imu.printSection('Processing VPR interactions')

    items = {}

    rawXmlPaths = glob.glob("%s/interactions/*.xml" % ds.getRawPath())
    for rawXmlPath in rawXmlPaths:
        # print "Processing interaction %s" % rawXmlPath

        with open(rawXmlPath) as f:
            interactions = xmltodict.parse(f, force_list=('Interaction', 'Part', 'PartDetail', 'Parameter')).itervalues().next()

        processCount = 0

        if interactions is not None:
            for interaction in interactions['Interaction']:
                name = interaction['Name']

                if name in items:
                    # print "When processing %s already found item with name %s" % (rawXmlPath, name)
                    pass
                else:
                    items[name] = interaction
                    processCount += 1

        # print "Processed %d interactions from %s" % (processCount, rawXmlPath)

    return items

def loadPartsFromXml(ds):
    """
    Given a dataset, load all the POLEN parts xml to dicts

    Returns a dictionary <part-name>:<part>
    """

    imu.printSection('Loading VPR parts')

    parts = {}

    rawPartsXmlPaths = glob.glob("%s/parts/*.xml" % ds.getRawPath())
    for rawPartXmlPath in rawPartsXmlPaths:
        with open(rawPartXmlPath) as f:
            partE = xmltodict.parse(f, force_list=('Property',)).itervalues().next()

        name = partE['Name']

        if name in parts:
            print "When processing %s already found part with name %s" % (rawPartXmlPath, name)
        else:
            parts[name] = partE

    return parts

def validateParts(parts):
    """
    Make sure that the parts data conforms to our expectations
    """

    imu.printSection('Validating VPR parts')

    organismNames = {}

    for part in parts.values():
        if 'Organism' in part:
            organismName = part['Organism']

            if organismName in organismNames:
                organismNames[organismName] += 1
            else:
                organismNames[organismName] = 1

        else:
            print 'Part %s has no organism data' % part['Name']

    print "Found distinct organism names:"
    for name, count in organismNames.iteritems():
        print "%s: %d" % (name, count)

def outputOrgItems(doc, vprOrgNamesToTaxonIds):
    """
    Output org items to the given document

    :param doc:
    :param vprOrgNamesToTaxonIds:
    :return: A dictionary of the items created, keyed by VPR organism name
    """
    items = {}

    for name, taxonId in vprOrgNamesToTaxonIds.iteritems():
        items[name] = createOrgItem(doc, taxonId)

    return items

def outputMetadataToItemsXml(doc):
    """
    Add InterMine metdata items (data source, dataset) to items XML.

    Returns the dataset item.
    """

    imu.printSection('Adding metadata items')
    
    dataSourceItem = doc.createItem('DataSource')
    dataSourceItem.addAttribute('name', 'POLEN')
    dataSourceItem.addAttribute('url', 'http://intbio.ncl.ac.uk/?projects=polen')
    doc.addItem(dataSourceItem)

    datasetItem = doc.createItem('DataSet')
    datasetItem.addAttribute('name', 'POLEN Parts')
    datasetItem.addAttribute('dataSource', dataSourceItem)
    doc.addItem(datasetItem)

    return datasetItem

def addOrgAttributeToPartItem(part, partItem, orgItemsByName):
    """
    Add the organism attribute to a part item
    :return:
    """

    name = part['Name']

    if 'Organism' in part:
        orgName = part['Organism']
        if orgName in orgItemsByName:
            orgItem = orgItemsByName[orgName]
        else:
            print 'Organism name [%s] for part %s not recognized, defaulting to Unknown' % (orgName, name)
            orgItem = orgItemsByName['Unknown']
    else:
        print 'No Organism name found for part %s, defaulting to Unknown' % name
        orgItem = orgItemsByName['Unknown']

    partItem.addAttribute('organism', orgItem)

def addPropertyAttributesToPartItem(part, partItem, goSynonyms):
    """
    Add property attributes to the part item that we recognized
    :param part:
    :param partItem:
    :param goSynonyms:
    :return:
    """

    if 'Property' in part:
        for propertyComponents in part['Property']:
            name = propertyComponents['Name']
            value = propertyComponents['Value']

            if name == 'has_function':
                partItem.addToAttribute('functions', createGoTermItem(doc, partItem.getAttribute('name'), value, goSynonyms, 'has_function'))
            elif name == 'participates_in':
                partItem.addToAttribute('participatesIn', createGoTermItem(doc, partItem.getAttribute('name'), value, goSynonyms, 'participates_in'))

def outputPartsToItemsXml(doc, ds, goDs, datasetItem, orgItemsByName, parts):
    """
    Given a set of parts, output InterMine items XML.
    """

    # We need to get a dictionary of go synonyms so that we can resolve those used in virtualparts
    imu.printSection('Loading GO synonyms')
    goSynonyms = go.getSynonoyms("%s/%s" % (goDs.getLoadPath(), 'go-basic.obo'))

    imu.printSection('Adding part items')
    print 'Adding %d parts' % (len(parts))

    for part in parts.values():
        name = part['Name']
        partItem = doc.createItem('Part')
        partItem.addAttribute('name', name)
        partItem.addAttribute('type', part['Type'])

        if 'Description' in part:
            partItem.addAttribute('description', part['Description'])

        # XXX: Reconstructing the uri here is far from ideal
        partItem.addAttribute('uri', 'http://www.virtualparts.org/part/%s' % name)

        addOrgAttributeToPartItem(part, partItem, orgItemsByName)

        if 'DesignMethod' in part:
            partItem.addAttribute('designMethod', part['DesignMethod'])
        else:
            print 'No DesignMethod set for part %s' % name

        # Sequence in all virtualparts.org XML has a mangled CDATA tag.
        # Let's see if Newcastle fix this before taking demangling measures ourselves
        # partItem.addAttribute('sequence', data['Sequence'])

        addPropertyAttributesToPartItem(part, partItem, goSynonyms)

        partItem.addToAttribute('dataSets', datasetItem)
        doc.addItem(partItem)

    doc.write('%s/items.xml' % ds.getLoadPath())

def createGoTermItem(doc, partName, id, goSynonyms, originalAttributeName):
    """Add a GOTerm item to a document and return"""
    
    # For some ineffable reason, virtualparts uses _ in their go term IDs rather than GO's own :
    id = id.replace('_', ':')

    if id in goSynonyms:
        print 'Replacing %s synonym %s with %s for part %s' % (originalAttributeName, id, goSynonyms[id], partName)
        id = goSynonyms[id]

    goTermItem = doc.createItem('GOTerm')
    goTermItem.addAttribute('identifier', id)
    doc.addItem(goTermItem)

    return goTermItem

def createOrgItem(doc, taxonId):
    """Add an organism item to a document and return"""

    orgItem = doc.createItem('Organism')
    orgItem.addAttribute('taxonId', taxonId)
    return doc.addItem(orgItem)

############
### MAIN ###
############
VPR_ORG_NAMES_TO_TAXON_IDS = {
    'Bacillus subtilis' : 1423,
    'Bacillus subtilis 168' : 224308,
    'Bacillus subtilis ATCC6633' : 96241,
    'Escherichia coli': 562,
    'Unknown': 0
}

parser = jargparse.ArgParser('Transform POLEN data into InterMine items XML')
parser.add_argument('colPath', help='path to the data collection')
args = parser.parse_args()

dc = sbd.Collection(args.colPath)
ds = dc.getSet('polen')
ds.startLogging(__file__)

parts = loadPartsFromXml(ds)
validateParts(parts)

model = dc.getModel()
doc = imm.Document(model)

dsItem = outputMetadataToItemsXml(doc)
orgItemsByName = outputOrgItems(doc, VPR_ORG_NAMES_TO_TAXON_IDS)
outputPartsToItemsXml(doc, ds, dc.getSet('go'), dsItem, orgItemsByName, parts)
loadInteractionsXml(ds)
