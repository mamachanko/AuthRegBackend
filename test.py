import unittest
import db
import user
import registration
import auth
import sqlite3
import os
import hashlib
import re
from config import DATABASE_PATH

class RegAndAuthBackendTests(unittest.TestCase):

	def setUp(self):
		if os.path.exists(DATABASE_PATH):
			os.remove(DATABASE_PATH)
		self.dbmanager = db.DBManager()
		self.dbmanager.createTables()
		self.dbmanager.insertGroup('admin')
		self.dbmanager.insertGroup('non-admin')

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

	def test_user_creation(self):
		"""
		Test basic user creation.
		"""
		self.assertFalse(user.exists(username = self.username))
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		self.assertTrue(user.exists(username = self.username))
		userobj = user.getUser(username = self.username)
		self.assertEquals(userobj.username, self.username)
		self.assertEquals(userobj.email, self.email)
		self.assertEquals(userobj.password, self.password)
		self.assertFalse(userobj.isActive())
		self.assertFalse(userobj.isLoggedIn())
		self.assertFalse(userobj.isLocked())

	def test_user_activation(self):
		userobj = user.User(username = self.username, email = self.email, password = self.password, authgroup = 'non-admin')
		userobj.save()
		sha1 = hashlib.sha1()
		sha1.update(userobj.username)
		wrongkey = sha1.hexdigest()
		userobj.activate(wrongkey)
		self.assertFalse(userobj.isActive())
		self.assertFalse(user.getUser(self.username).isActive())

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(RegAndAuthBackendTests)
	unittest.TextTestRunner(verbosity=2).run(suite)
