#!/usr/bin/python

# An incomplete scripts which aims to test certain integrity aspects of a synbiomine InterMine database

import argparse
import psycopg2
import sys

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

parser = MyParser('Check the integrity of the given InterMine database.')
parser.add_argument('dbName', help='name of the database to check.')
parser.add_argument('--dbUser', help='db user if this is different from the current')
parser.add_argument('--dbHost', help='db host if this is not localhost')
parser.add_argument('--dbPort', help='db port if this is not localhost')
parser.add_argument('--dbPass', help='db password if this is required')
args = parser.parse_args()

dbName = args.dbName
connString = "dbname=%s" % dbName

if args.dbUser:
  connString += " user=%s" % args.dbUser

if args.dbHost:
  connString += " host=%s" % args.dbHost

if args.dbPort:
  connString + " port=%s" % args.dbPort

if args.dbPass:
  connString += " password=%s" % args.dbPass

conn = psycopg2.connect(connString)

warnings = 0

cur = conn.cursor()
cur.execute("select count(*) from intermineobject;")
print "%s has %s InterMine objects" % (dbName, cur.fetchone()[0])

locatedonids = []
cur.execute("select distinct locatedonid from location order by locatedonid;")
for row in cur:
  if row[0] != None:
    locatedonids.append(row[0])

print "Found %d location.locatedonid entries.  Checking." % len(locatedonids)

for locatedonid in locatedonids:
#  print "Checking location.locatedonid %s" % locatedonid

  data = (locatedonid,)
  cur.execute("select * from bioentity where id=%s;", data)
  
  if cur.rowcount <= 0:
    warnings += 1
    print "WARNING: No BioEntity entry found for location.locatedonid %s" % locatedonid
"""
  else:
    for row in cur:
      print row
"""

cur.close()
conn.close()

print "%s warnings" % warnings
