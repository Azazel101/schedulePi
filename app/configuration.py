# -*- encoding: utf-8 -*-
import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():

	CSRF_ENABLED = True
	SECRET_KEY   = os.urandom(24)
	DEBUG = False
	SQLALCHEMY_TRACK_MODIFICATIONS 	= False

	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
