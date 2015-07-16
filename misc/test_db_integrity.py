#!/usr/bin/python

# An incomplete scripts which aims to test certain integrity aspects of a synbiomine InterMine database

import argparse
import psycopg2
import sys

objectClassesToCount = [ "intermineobject", "gene", "chromosome", "publication" ]

###############
### CLASSES ###
###############
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

###################
### SUBROUTINES ###
###################
def displayObjectCounts(dbCursor, objectClassesToCount):
  for classToCount in objectClassesToCount:
    dbCursor.execute("select count(*) from %s;" % classToCount)
    print "%s has %s %s rows" % (dbName, cur.fetchone()[0], classToCount)

def checkLocationLocatedonid(dbCursor):
  locatedonids = []
  dbCursor.execute("select distinct locatedonid from location order by locatedonid;")
  for row in cur:
    if row[0] != None:
      locatedonids.append(row[0])

  print "Found %d location.locatedonid entries.  Checking." % len(locatedonids)

  for locatedonid in locatedonids:
  #  print "Checking location.locatedonid %s" % locatedonid

    data = (locatedonid,)
    dbCursor.execute("select * from bioentity where id=%s;", data)
    
    if cur.rowcount <= 0:
      warnings += 1
      print "WARNING: No BioEntity entry found for location.locatedonid %s" % locatedonid

############
### MAIN ###
############
parser = MyParser('Check the integrity of the given InterMine database.')
parser.add_argument('dbname', help='name of the database to check.')
parser.add_argument('--dbuser', help='db user if this is different from the current')
parser.add_argument('--dbhost', help='db host if this is not localhost')
parser.add_argument('--dbport', help='db port if this is not localhost')
parser.add_argument('--dbpass', help='db password if this is required')
args = parser.parse_args()

dbName = args.dbname
connString = "dbname=%s" % dbName

if args.dbuser:
  connString += " user=%s" % args.dbuser

if args.dbhost:
  connString += " host=%s" % args.dbhost

if args.dbport:
  connString + " port=%s" % args.dbport

if args.dbpass:
  connString += " password=%s" % args.dbpass

conn = psycopg2.connect(connString)

warnings = 0

cur = conn.cursor()

displayObjectCounts(cur, objectClassesToCount)
checkLocationLocatedonid(cur);

cur.close()
conn.close()

print "%s warnings" % warnings
