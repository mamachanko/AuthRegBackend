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
from config import DATABASE_PATH

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
		self.assertFalse(user.exists(username = self.username))
		# create it
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		# now it should exist
		self.assertTrue(user.exists(username = self.username))
		# and now it should be retrievable from the db
		userobj = user.getUser(username = self.username)
		# with appropriate parameters being set
		self.assertEquals(userobj.username, self.username)
		self.assertEquals(userobj.email, self.email)
		self.assertEquals(userobj.password, self.password)
		self.assertFalse(userobj.isActive())
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(userobj.isLocked())

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
		self.assertFalse(user.getUser(self.username).isActive())

		# now activate with the right key
	 	userobj.activate(userobj.registration_key)
		# should be active
		self.assertTrue(userobj.isActive())
		# that should be in the db as well
		self.assertTrue(user.getUser(self.username).isActive())

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(RegAndAuthBackendTests)
	unittest.TextTestRunner(verbosity=2).run(suite)
