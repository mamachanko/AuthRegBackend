# /usr/bin/python

import datetime

DATABASE_PATH = './production.db'
EXPIRATION_PERIOD = datetime.timedelta(days=2)
LOCKOUT_PERIOD = datetime.timedelta(minutes=15)
FAILED_LOGIN_TOLERANCE = 5

# set up differently if testing
TESTING = True
if TESTING:
	DATABASE_PATH = './test.db'
	LOCKOUT_PERIOD = datetime.timedelta(seconds=2)
