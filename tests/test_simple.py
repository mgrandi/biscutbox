from tests.fixtures import \
(
    database_path,
    sqlite_cookie_jar,
    giant_list_of_cookies,
    giant_cookiejar_jsonl_path
)
from biscutbox.sqlite_cookie_jar import SqliteCookieJar

import pathlib
import itertools
from http.cookiejar import Cookie

class TestSimple:

    def test_simple(self,
        sqlite_cookie_jar:SqliteCookieJar):

        assert sqlite_cookie_jar != None


        test_cookie = Cookie(
            version=0,
            name="a",
            value="b",
            port=None,
            port_specified=False,
            domain="example.com",
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False)

        sqlite_cookie_jar.set_cookie(test_cookie)


    def test_load_giant_cookie_file(
        self,
        sqlite_cookie_jar:SqliteCookieJar,
        giant_list_of_cookies:list[Cookie]):

        assert sqlite_cookie_jar != None

        assert giant_list_of_cookies != None

        for iter_batch in itertools.batched(giant_list_of_cookies, 20):

            sqlite_cookie_jar.set_cookies(iter_batch)

        assert sqlite_cookie_jar._policy != None


        assert len(sqlite_cookie_jar) >= 0