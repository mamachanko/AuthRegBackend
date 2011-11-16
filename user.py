# /usr/bin/python

import hashlib
import random
import datetime
import db
from config import EXPIRATION_PERIOD, DATABASE_PATH, FAILED_LOGIN_TOLERANCE, LOCKOUT_PERIOD
from utils import *

class User(object):

	def __init__(self, username, password, email, authgroup, activated=None, expired=None, logged_in=None, failed_logins=None, locked=None, registration_key=None, key_expiration=None, locked_until=None):
		# set the user's details and credentials
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
		if locked_until == None:
			# if locked_until is not supplied it's valued doesn't matter
			# so it just should be set to a correct date value
			self.locked_until = datetime.datetime.now()
		else:
			self.locked_until = locked_until

		# if newUser is True the registration key needs to be transmitted to
		# the user's email and his password will be hashed instead of
		# storing it as real text
		if newUser:
			self.password = sha1Hash(self.password)
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

	def update(self):
		"""
		Propagates the current user state to the database via
		the database manager.
		"""
		# get the manager
		dbmanager = db.DBManager()
		# and to update
		dbmanager.updateUser(self)
		return True

	def activate(self, suppliedkey, now = datetime.datetime.now()):
		"""
		Activates a user if the supplied activation key is correct and
		the point in time is within the expiration period. If the key is
		incorrect the user will not be activated. If the expiration date
		is crossed the user will be expired.
		Returns True if activation is in time and the key is correct,
		False otherwise.
		"""
		# variable to store success of the activation attempt
		isokay = False
		if inTime(now, self.key_expiration):
			if suppliedkey == self.registration_key:
				self.activated = True
				# success
				isokay = not isokay
		else:
			self.expired = True
		# update user object
		self.update()
		return isokay

	def login(self, username, password):
		"""
		Login the user. The username and the password must both
		be provided as further security measure in case two user's
		incidentally share the same password.
		If values are correct the user will be logged in until he
		logs out. If the password is wrong the failed attempts will
		be counted and finally result in a locked account for some
		time. A correct login will reset the failed counter. It will
		also be reset when being locked out. The user will stay
		logged in until logout() is called.
		"""
		# check if the correct user is meant at all
		# or if the user is already logged in
		if username != self.username:
			# don't proceed in these cases
			return False
		# is the user allowed to login?
		if self.isLocked():
			# if not, don't proceed
			return False
		# otherwise check the password's credibility
		if sha1Hash(password) == self.password:
			# correct login
			self.logged_in = True
			self.failed_logins = 0
		else:
			# incorrect login
			self.logged_in = False
			self.failed_logins += 1
			if self.failed_logins > FAILED_LOGIN_TOLERANCE:
				self.locked = True
				self.locked_until = datetime.datetime.now() + LOCKOUT_PERIOD
		# propagate to db
		self.update()

	def logout(self):
		"""
		Logout the user.
		"""
		# this operation is not as critical so no checks are done
		self.logged_in = False
		self.update()

	def isActive(self):
		return self.activated

	def isLocked(self):
		"""
		Checks whether a user is locked by considering his
		locked status with respect to the lockout period.
		"""
		# if he's locked out
		if self.locked:
			# check whether the lockout period is still active
			now = datetime.datetime.now()
			if now > self.locked_until:
				# lockout period is over
				# unlock
				self.locked = False
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
