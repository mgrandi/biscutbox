import os
import sys
import pathlib
import logging

import pytest

import biscutbox
from biscutbox.sqlite_cookie_jar import SqliteCookieJar



logging.basicConfig(level="DEBUG", format="%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")


@pytest.fixture
def database_path():
    ''' a fixture to return a path to save the database to
    you can override it using direct test parametrization
    see https://docs.pytest.org/en/latest/how-to/fixtures.html#override-a-fixture-with-direct-test-parametrization
    '''

    return pathlib.Path.home() / "Temp/cookiedb.sqlite3"

@pytest.fixture
def sqlite_cookie_jar(database_path):
    ''' a fixture to set up a SqliteCookieJar with a database saved to a path
    returned by the database_path fixture
    '''

    cj = SqliteCookieJar(database_path=database_path)
    cj.connect()

    yield cj

    cj.close()
