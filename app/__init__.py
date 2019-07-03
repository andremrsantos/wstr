import os

from flask import Flask
from flask_cors import CORS
from peewee import SqliteDatabase

DEBUG = True
APPLICATION_ROOT = "/"
APP_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
DATABASE = os.path.join(APP_ROOT, "wstr.db")
UPLOAD_FOLDER = os.path.join(APP_ROOT, "upload")
MAX_CONTENT_PATH = 16 * 1024 * 1024

app = Flask(__name__, root_path=APP_ROOT)
app.config.from_object(__name__)
# Add cors support
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# Add SQLite support
db = SqliteDatabase(app.config["DATABASE"])
# Task reference
