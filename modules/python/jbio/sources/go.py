def getSynonoyms(goOboPath):
    """
    Extract the synonyms from a GO OBO file.
    """
    
    fcIds = set()
    synIds = {}
    currentFcId = None

    with open(goOboPath) as f:
        for line in f:
            line = line.strip()

            if line.find(':') > -1:
                (key, value) = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'id':
                    currentFcId = value
                    fcIds.add(currentFcId)
                elif key == 'alt_id':
                    if value in synIds:
                        raise Exception('Already found synonym %s => %s when trying to set up %s => %s' % (value, synIds[value], value, currentFcId))
                    else:
                        synIds[value] = currentFcId

#    for id in fcIds:
#        print id

    print("Got %d first class ids" % len(fcIds))
    print("Got %d synonyms" % len(synIds))

#    for synId, fcId in synIds.iteritems():
#        print "%s => %s" % (synId, fcId)

    synAndFcCount = 0
    for synId in list(synIds.keys()):
        if synId in fcIds:
            synAndFcCount += 1

    if synAndFcCount != 0:
        raise Exception("Got %d synonyms that were also first-class IDs when expecting 0" % (synAndFcCount))

    return synIds