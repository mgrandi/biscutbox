import os
import sys
import pathlib

import biscutbox
from biscutbox.sqlite_cookie_jar import SqliteCookieJar

import logging

db_dir = pathlib.Path.home() / "Temp/cookiedb.sqlite3"

logging.basicConfig(level="DEBUG", format="%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")

cj = SqliteCookieJar(database_path=db_dir)
cj.connect()
cj.close()