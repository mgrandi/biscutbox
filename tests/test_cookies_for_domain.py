from tests.fixtures import \
(
    database_path,
    sqlite_cookie_jar,
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


class TestCookiesForDomain():
    '''
    a class that will specialize in tests for the overriden method
    _cookie_for_domain
    '''


    def test_no_policy_single_cookie(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        runs a test for _cookies_for_domains with a sqlite cookie jar
        with no cookie policy attached
        '''

        test_cookie = create_simple_cookie("a", "b", "example.com")

        in_memory_sqlite_cookie_jar.set_cookie(test_cookie)

        # create request
        req = create_dummy_request(f"https://example.com", "GET")

        cookie_list = in_memory_sqlite_cookie_jar._cookies_for_domain("example.com", req)


        assert cookie_list != None
        assert len(cookie_list) == 1
        assert_cookie_equality(cookie_list[0], test_cookie)

    def test_no_policy_two_cookies_different_domains(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests _cookies_for_domains when you have multiple cookies
        (different domains)
        '''

        domain_one = "example.com"
        domain_two = "a.example.com"


        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # create requests
        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")
        req_domain_two = create_dummy_request(f"https://{domain_two}", "GET")

        # get the cookies for the first domain
        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        # we should only get one
        assert len(domain_one_result) == 1
        assert_cookie_equality(domain_one_result[0], test_cookie_one)

        # get the cookies for the second domain
        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        # we should only get one
        assert len(domain_two_result) == 1
        assert_cookie_equality(domain_two_result[0], test_cookie_two)

