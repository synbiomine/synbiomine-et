import glob
import os
import re

class Dataset:
    def __init__(self, basePath):
        self.basePath = basePath

        self.genbankPath = '%s/genbank' % self.basePath
        taxonsPath = '%s/taxons/taxons.txt' % self.basePath
        self._taxons = self._parseTaxons(taxonsPath)

    def _parseTaxons(self, taxonsPath):
        with open(taxonsPath) as f:
            self._taxons = set(f.read().strip().split())

    """
    Get organisms present as first class entities in this dataset
    Returns a dictionary of taxonId => name
    """
    def getOrganisms(self):
        orgs = {}

        for dirPath, dirNames, fileNames in os.walk(self.genbankPath):
            for fileName in fileNames:
                if fileName.endswith('_assembly_report.txt'):
                    with open(os.path.join(dirPath, fileName)) as f:
                        for line in f:
                            line = line.strip()
                            # print 'line: [%s]' % line
                            m = re.match('# Organism name:(.*)', line)
                            if m:
                                name = m.group(1).strip()
                            else:
                                m = re.match('# Taxid:(.*)', line)
                                if m:
                                    taxonId = m.group(1).strip()

                    orgs[taxonId] = name

        return orgs

    """
    Get the string list of taxons
    """
    def getTaxons(self):
        return set(self.taxons)

    """
    Get the taxons as a single ' ' separated string
    """
    def getTaxonsAsString(self):
        return ' '.join(self.taxons)
