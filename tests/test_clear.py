from tests.fixtures import \
(
    tempfolder_database_path,
    file_on_disk_sqlite_cookie_jar,
    giant_list_of_cookies,
    giant_cookiejar_jsonl_path,
    in_memory_sqlite_cookie_jar
)
from biscutbox.sqlite_cookie_jar import SqliteCookieJar
from biscutbox.sql_statements import SELECT_ALL_FROM_COOKIE_TABLE_BATCH_SIZE
from tests.test_utilities import \
(
    assert_cookie_equality,
    create_dummy_request,
    create_simple_cookie
)

from urllib.request import Request
import pathlib
import itertools
from http.cookiejar import Cookie


class TestClear():
    '''
    a class that will specialize in tests for the overriden method
    clear()
    '''


    def test_clear_no_arguments_simple_multiple_domains(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        test clear() with no arguments which clears all cookies
        '''

        domain_one = "example.com"
        domain_two = "a.example.com"


        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # call clear on the cookie jar with no arguments
        in_memory_sqlite_cookie_jar.clear()

        # assert that we have no more cookies
        assert len(in_memory_sqlite_cookie_jar) == 0
