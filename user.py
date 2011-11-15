# /usr/bin/python

import hashlib
import random
import datetime
import db
from config import EXPIRATION_PERIOD, DATABASE_PATH

def registrationKey(username):
	"""
	Generates a registration key by computing the value
	of SHA1 given the username and some random salt.
	"""
	sha1 = hashlib.sha1()
	sha1.update(str(random.random()))
	salt = sha1.hexdigest()[:4]
	sha1.update(username + salt)
	return sha1.hexdigest()

def exists(username):
	"""
	Check whether user with the given name already exists in the given db.
	"""
	dbmanager = db.DBManager()
	return dbmanager.userExists(username)

def getUser(username):
	"""
	Retrieve a user by it's name.
	"""
	dbmanager = db.DBManager()
	if not dbmanager.userExists(username):
		raise UserDoesNotExistException(username)
	else:
		details = dbmanager.getUser(username)[0][1:]
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
			'key_expiration' : datetime.datetime.strptime(details[5], "%Y-%m-%d %H:%M:%S.%f")}
		d['authgroup'] = dbmanager.getAuthGroupName(d['authgroupid'])
		d.pop('authgroupid')
		return User(**d)

class UserExistsException(Exception):
	"""
	An Exception representing that a user that should be saved already exists.
	"""
	def __init__(self, username):
		self.username = username

	def __str__(self):
		return repr(self.username) + 'already exists'

class UserDoesNotExistException(Exception):
	"""
	An Exception representing that a user does not yet exist.
	"""
	def __init__(self, username):
		self.username = username

	def __str__(self):
		return repr(self.username) + 'does not yet exist'

class User(object):

	def __init__(self, username, password, email, authgroup, activated=None, expired=None, logged_in=None, failed_logins=None, locked=None, registration_key=None, key_expiration=None):
		self.username = username
		self.email = email
		self.password = password
		self.authgroup = authgroup
		if activated == None:
			self.activated = False
		else:
			self.activated = activated
		if expired == None:
			self.expired = False
		else:
			self.expired = expired
		if logged_in == None:
			self.logged_in = False
		else:
			self.logged_in = logged_in
		if failed_logins == None:
			self.failed_logins = 0
		else:
			self.failed_logins = failed_logins
		if locked == None:
			self.locked = False
		else:
			self.locked = locked
		if registration_key == None:
			self.registration_key = registrationKey(username)
			newUser = True
		else:
			self.registration_key = registration_key
			newUser = False
		if key_expiration == None:
			self.key_expiration = datetime.datetime.now() + EXPIRATION_PERIOD
		else:
			self.key_expiration = key_expiration
	
		# if newUser is True the registration key needs to be transmitted to
		# the user's email somehow
		self.sendActivationEmail()

	def save(self):
		"""
		Initially saves a new user to the db.
		"""
		dbmanager = db.DBManager()
		if dbmanager.userExists(self.username):
			raise UserExistsException(self.username)
		else:
			dbmanager.insertUser(self)

	def inTime(self, date):
		if self.key_expiration > date:
			return True
		return False

	def activate(self, suppliedkey):
		if suppliedkey == self.registration_key and inTime(datetime.datetime.now()):
			self.activated = True
			return True
		return False

	def isActive(self):
		return self.activated

	def isLocked(self):
		return self.locked

	def isLoggedIn(self):
		return self.logged_in
	
	def isExpired(self):
		return self.expired

	def isAuthorized(self, resource):
		# Perform a look up of some kind
		# that maps the user authgroup onto resources
		# that particular group is allowed to access
		print "determine authorization for %s regarding %s's authgroup" % (resource, self.username)
		return True

	def sendActivationEmail(self):
		"""
		Transmit the registration key to the user's email adress.
		"""
		print 'sending registration_key: %s to %s' % (self.registration_key, self.email)
