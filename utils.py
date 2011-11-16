# /usr/bin/python

# Help functions and utilities

import hashlib
import datetime
import random

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
        An Exception representing that a user does not yet exist assuming he did.
        """
        def __init__(self, username):
                self.username = username

        def __str__(self):
                return repr(self.username) + 'does not yet exist'

def sha1Hash(value):
        """ 
        Returns the SHA1 hex digest of the supplied value.
        """
        sha1 = hashlib.sha1()
        sha1.update(value)
        return sha1.hexdigest()

def registrationKey(username):
        """ 
        Generates a registration key by computing the value
        of SHA1 given the username and some random salt.
        """
        # produce some salt
        salt = sha1Hash(str(random.random()))[:4]
        # hash the salted username 
        return sha1Hash(username + salt)

def inTime(date, expiration_date):
        """
        Check whether a date has not crossed a certain expiration date.
        """
	# datetime offers easy comparison operations on dates
        if expiration_date > date:
                return True
        return False

def bool2int(value):
	"""
        Maps Booleans onto integers: True -> 1, False -> 0
	Non-Booleans don't get mapped.
	"""
        if isinstance(value, bool):
		return int(value)
	return value

