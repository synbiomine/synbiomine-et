#!/usr/bin/env python

import requests

r = requests.get('http://synbis.bg.ic.ac.uk/synbisapi/searchlist/datasheet')

print r.text