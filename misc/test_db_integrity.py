#!/usr/bin/python

# An incomplete scripts which aims to test certain integrity aspects of a synbiomine InterMine database

import psycopg2

conn = psycopg2.connect("dbname=synbiomine2")

cur = conn.cursor()
cur.execute("select count(*) from intermineobject;")
print cur.fetchone()

cur.close()
conn.close()
