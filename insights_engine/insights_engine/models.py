import MySQLdb
from django.db import models

# Create your models here.

conn = MySQLdb.connect(host='localhost', port=3036, user='root', passwd='', db='insights_engine')

def run_query(query):
    conn_curosor = conn.cursor()
    conn_curosor.execute(query)
    data = conn_curosor.fetchall()
    conn_curosor.close()
    return data
