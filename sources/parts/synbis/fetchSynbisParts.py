#!/usr/bin/env python

import json
import requests

r = requests.get('http://synbis.bg.ic.ac.uk/synbisapi/searchlist/datasheet')
partsSummary = json.loads(r.text)

for partSummary in partsSummary:
    print partSummary['displayID']