class Dataset:
    def __init__(self, basePath):
        self.basePath = basePath
        self.taxonsPath = "%s/taxons/taxons.txt" % self.basePath

    """
    Get the string list of taxons
    """
    def getTaxons(self):
        with open(self.taxonsPath) as f:
            return f.read().strip().split()