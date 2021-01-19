#!/usr/bin python3

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from os import getenv

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


IS_DEV = getenv("IS_DEV", "0")


class Config(object):
    TESTING = getenv("IS_DEV", "0") == "1"
    DEBUG = IS_DEV
    SECRET_KEY = getenv('FLASK_SECRET_KEY')
    APPLICATION_ROOT = "/"
    SERVER_NAME = getenv("URL_LOCATION", None) if not IS_DEV else None
