from tests.fixtures import database_path, sqlite_cookie_jar

from http.cookiejar import Cookie

class TestSimple:
    def test_simple(self, sqlite_cookie_jar):

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