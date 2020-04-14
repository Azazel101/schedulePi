# -*- encoding: utf-8 -*-
import os

from flask            import Flask
from flask_sqlalchemy import SQLAlchemy

import threading
from app.tasks import threaded_task
#from flask_bcrypt     import Bcrypt

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config.from_object('app.configuration.Config')

db = SQLAlchemy  (app) # flask-sqlalchemy

# Import routing, models and Start the App
from app import views, models
