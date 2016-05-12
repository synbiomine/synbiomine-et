#!/usr/bin/python

# An incomplete script that aims to test certain integrity aspects of a synbiomine InterMine database

import argparse
import psycopg2
import sys

objectClassesToCount = [ "intermineobject", "gene", "chromosome", "publication" ]

warnings = 0

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

def checkGenes(dbCursor):
  warnings = 0

  # print "Checking genes"

  dbCursor.execute("select count(*) from gene where length is null;");
  count = cur.fetchone()[0]
  
  if count > 0:
    warnings += 1
    print "WARNING: Found %s genes with null length" % count

  return warnings

def checkLocations(dbCursor):
  warnings = 0
  locatedonids = []

  dbCursor.execute("select distinct locatedonid from location order by locatedonid;")
  for row in cur:
    if row[0] != None:
      locatedonids.append(row[0])

  print "Found %d location.locatedonid entries." % len(locatedonids)

  for locatedonid in locatedonids:
  #  print "Checking location.locatedonid %s" % locatedonid

    data = (locatedonid, )
    dbCursor.execute("select * from bioentity where id=%s;", data)
    
    if cur.rowcount <= 0:
      warnings += 1
      print "WARNING: No BioEntity entry found for location.locatedonid %s" % locatedonid

  return warnings

def checkPublications(dbCursor):
  warnings = 0

  # print "Checking publications"

  dbCursor.execute("select count(*) from publication where title is null;");
  count = cur.fetchone()[0]
  
  if count > 0:
    warnings += 1
    print "WARNING: Found %s publications with null title" % count

  return warnings

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

cur = conn.cursor()

displayObjectCounts(cur, objectClassesToCount)
warnings += checkGenes(cur)
warnings += checkLocations(cur)
warnings += checkPublications(cur)

cur.close()
conn.close()

print "%s warnings" % warnings
