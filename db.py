# /usr/bin/python

import sqlite3
from config import DATABASE_PATH
from utils import *
from user import User

# SQL statements without bindings
AUTHGROUP_TABLE_CREATION = 'CREATE TABLE authgroup (id INTEGER PRIMARY KEY, name TEXT UNIQUE);'
USER_TABLE_CREATION = """CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, password TEXT,
			authgroup_id NOT NULL REFERENCES authgroup, registration_key TEXT, key_expires_on TEXT,
			activated BOOLEAN, expired BOOLEAN, logged_in BOOLEAN, failed_logins INTEGER, locked BOOLEAN,
			locked_until TEXT)"""
GROUP_INSERT = 'INSERT INTO authgroup VALUES(null, ?)'
GROUP_GET_NAME = 'SELECT name FROM authgroup WHERE id = ?'
USER_INSERT = 'INSERT INTO user VALUES(null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
USER_EXISTS = 'SELECT * FROM user WHERE username = ?'
USER_GET = 'SELECT * FROM user WHERE username = ?'
USER_UPDATE = 'UPDATE user SET activated = ?, expired = ?, logged_in = ?, failed_logins = ?, locked = ?, locked_until = ? WHERE username = ?'

class DBManager(object):
	"""
	This class represents the interface to the database. It provides
	methods for storing, retrieving and updating users and authgroups.
	The database is an SQLite3 database.
	"""

	def __init__(self):
		self.conn = sqlite3.connect(DATABASE_PATH)
		self.cursor = self.conn.cursor()

	def __bool2int__(self, value):
		"""
		Maps Booleans onto integers: True -> 1, False -> 0
		Non-Booleans don't get mapped.
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
						user.failed_logins, user.locked, user.locked_until])
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

	def getUserDetails(self, username):
		"""
		Retrieve an existing user's details from the db.
		"""
		result = self.cursor.execute(USER_GET, (username,))
		return result.fetchall()

	def updateUser(self, userobj):
		"""
		Propagates the current state of the given user object to the database.
		"""
		bindings = (userobj.activated, userobj.expired, userobj.logged_in, userobj.failed_logins, userobj.locked, userobj.locked_until, userobj.username,)
		self.cursor.execute(USER_UPDATE, bindings)
		self.conn.commit()

	def getUser(self, username):
		"""
		Retrieve a user by it's name.
		"""
		# throw exception if it doesn't exist
		if not self.userExists(username):
			raise UserDoesNotExistException(username)
		else:
			# scrap the parameters and set up a dictionairy
			details = self.getUserDetails(username)[0][1:]
			d = {'username' : details[0],
                        'email' : details[1],
                        'password' : details[2],
                        'authgroupid' : details[3],
                        'activated' : bool(details[6]),
                        'expired' : bool(details[7]),
                        'logged_in' : bool(details[8]),
                        'failed_logins' : details[9],
                        'locked' : bool(details[10]),
                        'registration_key' : details[4],
                        'key_expiration' : datetime.datetime.strptime(details[5], "%Y-%m-%d %H:%M:%S.%f"),
			'locked_until' : datetime.datetime.strptime(details[11], "%Y-%m-%d %H:%M:%S.%f")}
			d['authgroup'] = self.getAuthGroupName(d['authgroupid'])
			d.pop('authgroupid')
			# return a user constructed from the dictionairy
			return User(**d)
