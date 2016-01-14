#!/usr/bin/python

from intermine.webservice import Service

service = Service('http://synbiomine.org/query/service')
query = service.new_query()
query.add_view('Gene.symbol', 'Gene.name') 
for row in query.results():
  print row
