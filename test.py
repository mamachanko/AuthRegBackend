import unittest
import db
import user
import registration
import auth
import sqlite3
import os

class RegAndAuthBackendTests(unittest.TestCase):

	def setUp(self):
		testdbpath = './test.db'
		if os.path.exists(testdbpath):
			os.remove(testdbpath)
		self.dbmanager = db.DBManager(testdbpath)
		self.dbmanager.createTables()		

		self.username = 'justaname'
		self.email = 'mail@website.de'
		self.password = '12345abc'

	def test_user_creation(self):
		self.assertFalse(user.exists(username = self.username))
		self.dbmanager.createUser(username = self.username,
		   		          email = self.email,
				          password = self.password)
		self.assertTrue(user.exists(username = self.username))
		userobj = user.getUser(username = self.username)
		self.assertEquals(userobj.username, self.username)
		self.assertEquals(userobj.email, self.email)
		self.assertEquals(userobj.password, self.password)
		self.assertFalse(userobj.isActive())

		

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(RegAndAuthBackendTests)
	unittest.TextTestRunner(verbosity=2).run(suite)
