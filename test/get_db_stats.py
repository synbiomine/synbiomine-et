#!/usr/bin/python

# Show database statistical information

import jargparse
import datetime
import json
import psycopg2
import sys
import texttable

###################
### SUBROUTINES ###
###################
def getCounts(conn, showEmpty = True):
  """Get counts of all InterMine database tables.
  
  Returns a dictionary of <table-name>:<count>
  
  conn - open database connection
  showEmpty - if true then 0 counts are also shown"""
  
  with conn.cursor() as cur:
    cur.execute("select table_name from information_schema.tables where table_schema='public' order by table_schema, table_name;")
    tables = cur.fetchall()
    results = {}
      
    for table in tables:
      table = table[0]
        
      cur.execute("select count(*) from %s" % table)
      count = cur.fetchone()[0]
    
      if showEmpty or count > 0:
        results[table] = count
        # prettySummaryTable.add_row([table, count])
        # print "%s: %s" % (table, count)
        
    return results
  
def getMetadataSizes(conn, showEmpty = True):
  """Get sizes of all InterMine metadata entries
  
  Returns a dictionary of <name>:<size>
  
  conn - open database connection
  showEmpty - if true then 0 sizes are also shown"""    
  with conn.cursor() as cur:
    cur.execute("select key, length(value), length(blob_value) from intermine_metadata;")
    entries = cur.fetchall()
    results = {}
    
    for entry in entries:
      (name, size, blobSize) = entry
      
      size = max(size, blobSize)
      
      if showEmpty or size > 0:
        results[name] = size
      
  return results                
  
def outputJson(name, host, counts, metadataSizes, fileName):
  now = datetime.datetime.now()
  jsonData = { 'name' : name, 'host' : host, 'date' : now.isoformat(), 'tables' : counts, 'metadata' : metadataSizes }
  
  if fileName == None:
    fileName = "%s-%s-%s" % (name, host, now.isoformat())

  with open(fileName, 'w') as f:
    f.write(json.dumps(jsonData, indent=4))
    
def generatePrettyPrintTable(headers):
  table = texttable.Texttable()
  table.set_deco(texttable.Texttable.VLINES | texttable.Texttable.HLINES)
  table.add_row(headers)
  
  return table  

def prettyPrintCounts(counts):
  """Pretty print counts"""
  
  consoleTable = generatePrettyPrintTable(['Table', 'Entries'])
  
  for table in sorted(counts.keys()):
    consoleTable.add_row([table, counts[table]])

  print consoleTable.draw()
  
def prettyPrintMetadataSizes(sizes):
  """Pretty print metadata sizes"""
  
  consoleTable = generatePrettyPrintTable(['Name', 'Size'])

  for entry in sorted(sizes.keys()):
    consoleTable.add_row([entry, sizes[entry]])

  print consoleTable.draw()  

############
### MAIN ###
############
parser = jargparse.ArgParser('Display object and metadata counts for an InterMine database.  By default does not show tables with zero rows.')
parser.add_argument('dbname', help='name of the database.')
parser.add_argument('--dbuser', help='db user if this is different from the current')
parser.add_argument('--dbhost', help='db host if this is not localhost')
parser.add_argument('--dbport', help='db port if this is not localhost')
parser.add_argument('--dbpass', help='db password if this is required')
parser.add_argument('-a', '--all', action="store_true", help='show tables with zero rows')
parser.add_argument('-o', '--output', nargs='?', default=argparse.SUPPRESS, help='write results to file in JSON format.')
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

counts = getCounts(conn, showEmpty = args.all)
metadataSizes = getMetadataSizes(conn, showEmpty = args.all)

conn.close()

if hasattr(args, 'output'):
  outputJson(dbName, dbHost, counts, metadataSizes, args.output)
else:
  prettyPrintCounts(counts)
  print
  prettyPrintMetadataSizes(metadataSizes)
