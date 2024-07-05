from tests.fixtures import database_path, sqlite_cookie_jar


class TestSimple:
    def test_simple(self, sqlite_cookie_jar):

        assert sqlite_cookie_jar != None