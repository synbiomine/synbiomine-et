import urllib.parse as up

def _getImNameParts(rdfName, rdfNsToImNameMap = None):
    """
    Get name parts from an RDF name.

    :param rdfName:
    :param rdfNsToImNameMap:
        Either None or a map of RDF namespaces to InterMine names
    :return:
        (name-part-1, name-part-2)
        For name-part-1, if nsToImNameMap was given and the RDF namespace matches an entry, then the IM name is returned
        Otherwise name-part-1 is the first part of the hostname before the period.
        For name-part-2, this is the fragment part of the RDF name, or the last component of the path if there is no
        fragment.
    """

    _, host, path, _, _, fragment = up.urlparse(rdfName)

    a = None

    if rdfNsToImNameMap is not None:
        if fragment != '':
            ns = host + path
        else:
            ns = host + path.rsplit('/')[0]
        #print('NS [%s]' % ns)
        if ns in rdfNsToImNameMap:
            a = rdfNsToImNameMap[ns]

    if a is None:
        a = host.split('.')[0]

    if fragment != '':
        b = fragment
    else:
        b = path.split('/')[-1]

    return a, b

def generateImClassName(rdfName, rdfNsToImNameMap):
    """
    For IM class names, we're just going to directly weld the two parts from _getImNameParts() together.
    """

    (a, b) = _getImNameParts(rdfName, rdfNsToImNameMap)

    return a + b

def generateImPropertyName(rdfName):
    """
    For IM property names, we're going to weld the two parts from _getImNameParts() together with a _.
    This is to avoid an issue if class and individual names are the same
    (this punning is not supported by the owlready library that we're using).
    """

    (a, b) = _getImNameParts(rdfName)

    return a + '_' + b