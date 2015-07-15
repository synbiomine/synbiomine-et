#!/usr/bin/python

# An incomplete scripts which aims to test certain integrity aspects of a synbiomine InterMine database

import psycopg2

dbName = "synbiomine2"
conn = psycopg2.connect("dbname=%s" % dbName)

cur = conn.cursor()
cur.execute("select count(*) from intermineobject;")
print "%s has %s InterMine objects" % (dbName, cur.fetchone()[0])

cur.execute("select distinct locatedonid from location order by locatedonid;")
for row in cur:
  locatedonid = row[0]
  if locatedonid != None:
    print "Found location.locatedonid %s" % locatedonid

cur.close()
conn.close()
