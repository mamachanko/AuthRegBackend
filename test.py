import unittest
import db
import user
import registration
import auth
import sqlite3
import os
import hashlib
import re
import datetime
import time
from config import DATABASE_PATH, EXPIRATION_PERIOD, FAILED_LOGIN_TOLERANCE, LOCKOUT_PERIOD
from utils import *

class RegAndAuthBackendTests(unittest.TestCase):

	def setUp(self):
		"""
		Set up the test db and basic user details for testing.
		"""
		# if the test db does not yet exist, create it
		if os.path.exists(DATABASE_PATH):
			os.remove(DATABASE_PATH)
		# create the dbmanager
		self.dbmanager = db.DBManager()
		# and release table creation statements
		self.dbmanager.createTables()
		# set up two authgroups by default, non-admin and admin
		self.dbmanager.insertGroup('admin')
		self.dbmanager.insertGroup('non-admin')

		# basic user credentials for testing
		self.username = 'justaname'
		self.email = 'mail@website.de'
		self.password = '12345abc'

	def test_activation_key(self):
		"""
		Test the activation key's basic propertievshe and whether
		the key cannot easily be forged, if the hash function is known.
		"""
		# get a key for a username
		key = user.registrationKey(self.username)
		# check it's composure and length
		key_regex = re.compile('^[a-f0-9]{40}$')
		self.assertEqual(len(key_regex.findall(key)), 1)

		# check that it cannot be forged easily
		# by simply computing the username's sha1 hash
		sha1 = hashlib.sha1()
		sha1.update(self.username)
		forgedkey = sha1.hexdigest()
		self.assertNotEqual(key, forgedkey)

	def test_helper_functions(self):
                self.assertEquals(self.dbmanager.__bool2int__(True), 1)
		self.assertEquals(self.dbmanager.__bool2int__(False), 0)
		self.assertEquals(self.dbmanager.__bool2int__('astring'), 'astring')

		date = datetime.datetime.now()
		expiration_date = date + datetime.timedelta(days=2)
		self.assertTrue(user.inTime(date, expiration_date))
		self.assertTrue(user.inTime(date + datetime.timedelta(days=1), expiration_date))
		self.assertFalse(user.inTime(date + datetime.timedelta(days=2), expiration_date))
		self.assertFalse(user.inTime(date + datetime.timedelta(days=2, minutes=1), expiration_date))

	def test_user_creation(self):
		"""
		Test user creation.
		"""
		# user should not yet exist
		self.assertFalse(self.dbmanager.userExists(username = self.username))
		# create it
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		# now it should exist
		self.assertTrue(self.dbmanager.userExists(username = self.username))
		# and now it should be retrievable from the db
		userobj = self.dbmanager.getUser(username = self.username)
		# with appropriate parameters being set
		self.assertEquals(userobj.username, self.username)
		self.assertEquals(userobj.email, self.email)
		self.assertFalse(userobj.isActive())
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(userobj.isLocked())

		# the user's password should not be stored as clear text
		self.assertNotEquals(userobj.password, self.password)
		# and should have propageted to the db
		self.assertNotEquals(self.dbmanager.getUser(self.username).password, self.password)
		# instead it should be stored as the password's hash
		self.assertEquals(userobj.password, sha1Hash(self.password))
		# and should have propageted to the db
		self.assertEquals(self.dbmanager.getUser(self.username).password, sha1Hash(self.password))

	def test_user_activation(self):
		"""
		Test user activation.
		"""
		# create a user
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		# try to activate him with a wrong key
		sha1 = hashlib.sha1()
		sha1.update(userobj.username)
		wrongkey = sha1.hexdigest()
		userobj.activate(wrongkey)
		# he should not be active
		self.assertFalse(userobj.isActive())
		# that should be in the db as well
		self.assertFalse(self.dbmanager.getUser(self.username).isActive())

		# the right key
		rightkey = userobj.registration_key

		# check whether the expiration period works
		# and restricts activation to the expiration period
		later = datetime.datetime.now() + EXPIRATION_PERIOD
		userobj.activate(rightkey, later)
		# should not be active
		self.assertFalse(userobj.isActive())

		# now activate with the right key
		userobj.activate(rightkey)
		# should be active
		self.assertTrue(userobj.isActive())
		# that should be in the db as well
		self.assertTrue(self.dbmanager.getUser(self.username).isActive())

	def test_login(self):
		"""
		Test login and logout of a user.
		"""
		# create a user
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		# shouldn't be logged in, because not active
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLoggedIn())
		# activate
		userobj.activate(userobj.registration_key)
		# still shouldn't be logged in
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLoggedIn())

		# try to login correctly
		userobj.login(username = self.username, password = self.password)
		self.assertTrue(userobj.isLoggedIn())
		self.assertTrue(self.dbmanager.getUser(username = userobj.username).isLoggedIn())
		# and logout
		userobj.logout()
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLoggedIn())

		# try with wrong username
		userobj.login(username = 'notjustaname', password = self.password)
		# shouldn't be logged in
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLoggedIn())

		# try with wrong password
		trials = userobj.failed_logins
		userobj.login(username = self.username, password = 'wrongpass')
		# shouldn't be logged in
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLoggedIn())
		# trial counter should have been incremented
		self.assertEquals(trials+1, userobj.failed_logins)
		self.assertEquals(self.dbmanager.getUser(username = userobj.username).failed_logins, trials+1)

		# test locking
		# login and out to reset counter
		userobj.login(self.username, self.password)
		userobj.logout()
		# is reset?
		self.assertEquals(userobj.failed_logins, 0)
		self.assertEquals(self.dbmanager.getUser(username = userobj.username).failed_logins, 0)
		# lock user by attempting to login with wrong password several times
		for i in range(FAILED_LOGIN_TOLERANCE+1):
			userobj.login(username = self.username, password = 'wrongpass%s' % i)
		self.assertTrue(userobj.isLocked())
		self.assertTrue(self.dbmanager.getUser(username = userobj.username).isLocked())
		# should unlock after LOCKOUT_PERIOD
		seconds = LOCKOUT_PERIOD.total_seconds()
		print 'wait %s secs for unlock' % seconds
		time.sleep(seconds)
		self.assertFalse(userobj.isLocked())
		self.assertFalse(self.dbmanager.getUser(username = userobj.username).isLocked())


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(RegAndAuthBackendTests)
	unittest.TextTestRunner(verbosity=2).run(suite)
