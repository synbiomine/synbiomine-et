#!/usr/bin/python

# Show database statistical information

import argparse
import datetime
import json
import psycopg2
import sys
import texttable

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

def outputJson(name, host, results, fileName):
  now = datetime.datetime.now()
  jsonData = { 'name' : name, 'host' : host, 'date' : now.isoformat(), 'tables' : results }
  
  if fileName == None:
    fileName = "%s-%s-%s" % (name, host, now.isoformat())

  with open(fileName, 'w') as f:
    f.write(json.dumps(jsonData, indent=4))

def prettyPrintResults(results):
  # Pretty print results
  prettySummaryTable = texttable.Texttable()
  prettySummaryTable.set_deco(texttable.Texttable.VLINES | texttable.Texttable.HLINES)
  prettySummaryTable.add_row(['Table', 'Entries'])

  for table in sorted(results.keys()):
    prettySummaryTable.add_row([table, results[table]])

  print prettySummaryTable.draw()

############
### MAIN ###
############
parser = MyParser('Display statistical information about the given InterMine database.  By default does not show tables with zero rows.')
parser.add_argument('dbname', help='name of the database.')
parser.add_argument('--dbuser', help='db user if this is different from the current')
parser.add_argument('--dbhost', help='db host if this is not localhost')
parser.add_argument('--dbport', help='db port if this is not localhost')
parser.add_argument('--dbpass', help='db password if this is required')
parser.add_argument('-a', '--all', action="store_true", help='show tables with zero rows')
parser.add_argument('-o', '--output', nargs='?', help='write results to file in JSON format.')
args = parser.parse_args()

dbName = args.dbname
connString = "dbname=%s" % dbName

if args.dbuser:
  connString += " user=%s" % args.dbuser

dbHost = 'localhost'
if args.dbhost:
  dbHost = args.dbhost
  connString += " host=%s" % dbHost

if args.dbport:
  connString + " port=%s" % args.dbport

if args.dbpass:
  connString += " password=%s" % args.dbpass

conn = psycopg2.connect(connString)

cur = conn.cursor()

cur.execute("select table_name from information_schema.tables where table_schema='public' order by table_schema, table_name;")
tables = cur.fetchall()
results = {}

for table in tables:
  table = table[0]
  
  cur.execute("select count(*) from %s" % table)
  count = cur.fetchone()[0]

  if args.all or count > 0:
    results[table] = count
    # prettySummaryTable.add_row([table, count])
    # print "%s: %s" % (table, count)

cur.close()
conn.close()

if hasattr(args, 'output'):
  outputJson(dbName, dbHost, results, args.output)
else:
  prettyPrintResults(results)
