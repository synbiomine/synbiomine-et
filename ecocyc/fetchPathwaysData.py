#!/usr/bin/python

import httplib

c = httplib.HTTPConnection("biocyc.org")
c.request("GET", "ECOLI/class-instances?object=Pathways")
r = c.getresponse()
print r.status, r.reason
print "[%s]" % r.read()
c.close()
