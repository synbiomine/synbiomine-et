#!/usr/bin/python

# Show database statistical information

import argparse
import psycopg2
import sys

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

############
### MAIN ###
############
parser = MyParser('Display statistical information about the given InterMine database.')
parser.add_argument('dbname', help='name of the database.')
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

cur.execute("select table_name from information_schema.tables where table_schema='public' order by table_schema, table_name;")
tables = cur.fetchall()

for table in tables:
  table = table[0]
  
  cur.execute("select count(*) from %s" % table)
  print "%s: %s" % (table, cur.fetchone()[0])

cur.close()
conn.close()
