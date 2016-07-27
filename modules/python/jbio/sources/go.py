import sys

"""
Extract the synonyms from a GO OBO file.
"""
def getSynonoyms(goOboPath):
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
                        print "ERROR: Already found synonym %s => %s when trying to set up %s => %s" % (value, synIds[value], value, currentFcId)
                        sys.exit(2)
                    else:
                        synIds[value] = currentFcId

    for id in fcIds:
        print id

    print "Got %d first class ids" % len(fcIds)
    print "Got %d synonyms" % len(synIds)

    synAndFcCount = 0
    for synId in synIds.keys():
        if synId in fcIds:
            synAndFcCount += 1

    print "Got %d synonyms that were also first-class IDs" % (synAndFcCount)