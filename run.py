# -*- encoding: utf-8 -*-

from app import app, db
from app.views import initialize
from app.configuration import Config

if __name__ == "__main__":
    if not Config.DEBUG: initialize()
    app.run(host='0.0.0.0', port=80)
