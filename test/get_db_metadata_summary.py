#!/usr/bin/python

import psycopg2
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.utils as imu

############
### MAIN ###
############
parser = imu.ArgParser('Show information about the intermine_metadata.')
parser.add_argument('dbname', help='name of the database.')
parser.add_argument('--dbuser', help='db user if this is different from the current')
parser.add_argument('--dbhost', help='db host if this is not localhost')
parser.add_argument('--dbport', help='db port if this is not localhost')
parser.add_argument('--dbpass', help='db password if this is required')
parser.add_argument('-a', '--all', action="store_true", help='show tables with zero rows')
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
cur.execute("select key, length(value), length(blob_value) from intermine_metadata;")
rows = cur.fetchall()

for row in rows:
  print row

cur.close()
conn.close()
