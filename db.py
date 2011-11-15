# /usr/bin/python

import sqlite3
from config import DATABASE_PATH

AUTHGROUP_TABLE_CREATION = """CREATE TABLE authgroup
(id INTEGER PRIMARY KEY,
name TEXT UNIQUE);"""

USER_TABLE_CREATION = """CREATE TABLE user
(id INTEGER PRIMARY KEY,
username TEXT UNIQUE,
email TEXT,
password TEXT,
authgroup_id NOT NULL REFERENCES authgroup,
registration_key TEXT,
key_expires_on TEXT,
activated BOOLEAN,
expired BOOLEAN,
logged_in BOOLEAN,
failed_logins INTEGER,
locked BOOLEAN)"""

GROUP_INSERT = 'INSERT INTO authgroup VALUES(null, ?)'
GROUP_GET_NAME = 'SELECT name FROM authgroup WHERE id = ?'
USER_INSERT = 'INSERT INTO user VALUES(null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
USER_EXISTS = 'SELECT * FROM user WHERE username = ?'
USER_GET = 'SELECT * FROM user WHERE username = ?'

class DBManager(object):

	def __init__(self):
		self.conn = sqlite3.connect(DATABASE_PATH)
		self.cursor = self.conn.cursor()

	def __bool2int__(self, value):
		"""
		Maps Booleans onto integers: True -> 1, False -> 0
		Non-Booleans don't get mapped.

		#doctest
		>>> dbmanager = DBManager('./test.db')
		>>> DBManager.__bool2int__(dbmanager, True)
		1
		>>> DBManager.__bool2int__(dbmanager, False)
		0
		>>> DBManager.__bool2int__(dbmanager, 'astring')
		'astring'
		"""
		if isinstance(value, bool):
			return int(value)
		return value

	def createTables(self):
		"""
		Creates the two tables necessary for the backend: authgroup, user
		"""
		self.cursor.execute(AUTHGROUP_TABLE_CREATION)
		self.cursor.execute(USER_TABLE_CREATION)
		self.conn.commit()

	def insertGroup(self, name):
		"""
		Inserts an authorization group into the database
		"""
		self.cursor.execute(GROUP_INSERT, (name,))
		self.conn.commit()

	def insertUser(self, user):
		"""
		Inserts a user into the database.
		"""
		authgroup = user.authgroup
		authgroup_id = self.cursor.execute('SELECT id FROM authgroup WHERE name = ?', (authgroup,)).fetchone()[0]
		bindings = map(self.__bool2int__, [user.username, user.email, user.password, authgroup_id, user.registration_key,
						str(user.key_expiration), user.activated, user.expired, user.logged_in,
						user.failed_logins, user.locked])
		self.cursor.execute(USER_INSERT, bindings)
		self.conn.commit()

	def userExists(self, username):
		"""
		Checks whether a user with the given username is already present in the database.
		"""
		result = self.cursor.execute(USER_EXISTS, (username,)).fetchall()
		if len(result) > 0:
			return True
		return False

	def getAuthGroupName(self, groupid):
		"""
		Returns the name of an authgroup by it's id.
		"""
		result = self.cursor.execute(GROUP_GET_NAME, (groupid,))
		return result.fetchone()[0]

	def getUser(self, username):
		"""
		Retrieve an existing user by it's name and return the details.
		"""
		result = self.cursor.execute(USER_GET, (username,))
		return result.fetchall()
