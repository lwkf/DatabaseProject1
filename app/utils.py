import sqlite3
from flask_pymongo import PyMongo
from flask import current_app, g
from config import Config

web_config = Config()

def get_db():
    db = getattr(g, "_mongo_db", None)
    if db is None:
        db = g._mongo_db = PyMongo( app = current_app, uri = web_config.MONGODB_URI ).db
    return db