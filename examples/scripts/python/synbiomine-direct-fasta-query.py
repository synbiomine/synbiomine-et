#!/usr/bin/python

import requests

#endpoint = "http://synbiomine.org/query/service/query/results"
endpoint = 'http://www.flymine.org/query/service/query/results/fasta'
# query = '<query name="short genes on the X chromosome" model="genomic" view="Gene.id"> <constraint path="Gene.chromosome.primaryIdentifier" op="=" value="X"/> <constraint path="Gene.length" op="&lt;" value="1000"/> </query>'
query = '''<query model="genomic" view="Gene.id">
<constraint path="Gene.organism.taxonId" op="LOOKUP" value="224308"/>
<constraint path="Gene.length" op="&lt;" value="1000"/>
</query>'''
params = {'query':query}

response = requests.post(endpoint, params=params)
print response.text
