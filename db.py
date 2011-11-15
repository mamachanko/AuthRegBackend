# /usr/bin/python

import sqlite3

AUTHGROUP_TABLE_CREATION = """CREATE TABLE authgroup (id INTEGER PRIMARY KEY, name TEXT);"""

USER_TABLE_CREATION = """CREATE TABLE user
		(id INTEGER PRIMARY KEY,
		username TEXT,
		email TEXT,
		authgroup_id NOT NULL REFERENCES authgroup,
		registration_key TEXT
		activated BOOLEAN,
		expired BOOLEAN,
		logged_in BOOLEAN,
		locked BOOLEAN)"""

class DBManager(object):

	def __init__(self, dbpath=''):
		conn = sqlite3.connect(dbpath)
		self.cursor = conn.cursor()

	def createTables(self):
		self.cursor.execute(AUTHGROUP_TABLE_CREATION)
		self.cursor.execute(USER_TABLE_CREATION)
		
