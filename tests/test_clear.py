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

        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")
        req_domain_two = create_dummy_request(f"https://{domain_two}", "GET")


        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # assert cookies are there

        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 1
        assert_cookie_equality(domain_one_result[0], test_cookie_one)

        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result) == 1
        assert_cookie_equality(domain_two_result[0], test_cookie_two)

        # call clear on the cookie jar with no arguments
        in_memory_sqlite_cookie_jar.clear()

        # assert that we have no more cookies
        assert len(in_memory_sqlite_cookie_jar) == 0

        # assert cookies are gone

        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 0

        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result) == 0


    def test_clear_one_argument_domain_provided(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        test clear() with a domain argument that is non null
        '''

        domain_one = "example.com"
        domain_two = "a.example.com"

        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")
        req_domain_two = create_dummy_request(f"https://{domain_two}", "GET")

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # assert cookies are there

        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 1
        assert_cookie_equality(domain_one_result[0], test_cookie_one)

        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result) == 1
        assert_cookie_equality(domain_two_result[0], test_cookie_two)

        # call clear with one of the domains and assert we only remove one cookie, not both

        in_memory_sqlite_cookie_jar.clear(domain=domain_one)

        assert len(in_memory_sqlite_cookie_jar) == 1

        # cookies for domain one should be claered
        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 0

        # cookies for domain two should be present
        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result) == 1
        assert_cookie_equality(domain_two_result[0], test_cookie_two)