import urllib.parse as up

def _getNameParts(rdfName):
    _, host, path, _, _, fragment = up.urlparse(rdfName)
    a = host.split('.')[0]
    if fragment != '':
        b = fragment
    else:
        b = path.split('/')[-1]

    return (a, b)

def generateImClassName(rdfName):
    """
    We're gonna do something super hacky and generate InterMine names from RDF URLs by welding the first dotted part
    of the host name to the last part or fragment (if available) of the path
    """

    (a, b) = _getNameParts(rdfName)

    return a + b

def generateImPropertyName(rdfName):
    """
    We're gonna do something super hacky and generate InterMine names from RDF URLs by welding the first dotted part
    of the host name to the last part or fragment (if available) of the path.  But this with an _ to distinguish
    between class and individual names (this punning is not supported by the owlready library that we're using and
    it's simplest just to make the 2 names distinct right now.
    """

    (a, b) = _getNameParts(rdfName)

    return a + '_' + b