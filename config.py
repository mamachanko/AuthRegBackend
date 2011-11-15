# /usr/bin/python

import datetime

TESTING = True

if TESTING:
	DATABASE_PATH = './test.db'
else:
	DATABASE_PATH = './production.db'

EXPIRATION_PERIOD = datetime.timedelta(days=2)
