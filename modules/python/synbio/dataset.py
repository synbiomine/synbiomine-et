class Dataset:
    def __init__(self, basePath):
        self.basePath = basePath

        taxonsPath = "%s/taxons/taxons.txt" % self.basePath
        self._taxons = self._parseTaxons(self, taxonsPath)

    def _parseTaxons(self, taxonsPath):
        with open(taxonsPath) as f:
            self._taxons = set(f.read().strip().split())

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
