import os
import sys
import pathlib
import logging
import json
from http.cookiejar import Cookie

import pytest

import biscutbox
from biscutbox.sqlite_cookie_jar import SqliteCookieJar



logging.basicConfig(level="DEBUG", format="%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")


@pytest.fixture(scope="function")
def database_path(tmp_path_factory:pytest.TempPathFactory) -> pathlib.Path:
    ''' a fixture to return a path suitable to store the database in. this will use a temporary path
    provided by the tmp_path_factory fixture, and is scoped currently to be 'function', so it will be a new database
    every time.

    https://docs.pytest.org/en/latest/how-to/tmp_path.html#the-tmp-path-factory-fixture
    '''
    fn = tmp_path_factory.mktemp("data") / "cookiedb.sqlite3"

    return fn

@pytest.fixture
def giant_cookiejar_jsonl_path() -> pathlib.Path:
    '''a fixture to return a path to load a ginat jsonl file that
    has cookies
    '''

    return pathlib.Path.home() / "Temp/giant_cookiejar_file.jsonl"

@pytest.fixture
def giant_list_of_cookies(giant_cookiejar_jsonl_path:pathlib.Path) -> list[Cookie]:
    '''
    this loads a giant JSONL dump of the the cookiejar

    it seems to be in this format

    each line is a complete JSON object
    each line's JSON object is:

    {
      "domain": "example.com",
      "cookies": {
        "PATH_HERE": {
          "COOKIE_NAME_HERE_1": {
            "version": 0,
            "name": "COOKIE_NAME_HERE_1",
            "value": "VALUE HERE",
            "port": null,
            "port_specified": false,
            "domain": "example.com",
            "domain_specified": false,
            "domain_initial_dot": false,
            "path": "PATH_HERE",
            "path_specified": true,
            "secure": false,
            "expires": null,
            "discard": true,
            "comment": null,
            "comment_url": null,
            "_rest": {},
            "rfc2109": false
          },
          COOKIE_NAME_HERE_2: {
            // ...
          }
        }
      }
    }

    you basically just need to just to get access to the the object
    that has all of the cookie properties and ignore all the various keys

    '''

    result_list = list()

    with open(giant_cookiejar_jsonl_path, "r", encoding="utf-8") as f:

        while True:
            iterline = f.readline()
            if not iterline:
                break

            cookie_dict = json.loads(iterline)

            domain = cookie_dict["domain"]
            for iter_path, iter_path_dict in cookie_dict["cookies"].items():

                # some entries are empty so skip those
                if not iter_path_dict:
                    continue

                for iter_cookie_name, iter_cookie_dict in iter_path_dict.items():

                    c = iter_cookie_dict

                    iter_cookie = Cookie(
                        version=c["version"],
                        name=c["name"],
                        value=c["value"],
                        port=c["port"],
                        port_specified=c["port_specified"],
                        domain=c["domain"],
                        domain_specified=c["domain_specified"],
                        domain_initial_dot=c["domain_initial_dot"],
                        path=c["path"],
                        path_specified=c["path_specified"],
                        secure=c["secure"],
                        expires=c["expires"],
                        discard=c["discard"],
                        comment=c["comment"],
                        comment_url=c["comment_url"],
                        rest=c["_rest"],
                        rfc2109=c["rfc2109"])

                    result_list.append(iter_cookie)
    return result_list


@pytest.fixture
def in_memory_sqlite_cookie_jar(database_path) -> SqliteCookieJar:
    ''' a fixture to set up a SqliteCookieJar with a database that is only in RAM
    '''

    cj = SqliteCookieJar(database_path=":memory:")
    cj.connect()

    yield cj

    cj.close()



@pytest.fixture
def sqlite_cookie_jar(database_path) -> SqliteCookieJar:
    ''' a fixture to set up a SqliteCookieJar with a database saved to a path
    returned by the database_path fixture
    '''

    cj = SqliteCookieJar(database_path=database_path)
    cj.connect()

    yield cj

    cj.close()
