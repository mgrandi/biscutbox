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


class TestCookiesForRequest():
    '''
    a class that will specialize in tests for the overriden method
    _cookies_for_request
    '''

    def test_no_policy_two_cookies_different_subdomains(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests _cookies_for_request when you have multiple cookies
        (different subdomains)
        '''

        domain_one = "example.com"
        domain_two = "a.example.com"


        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # create a dummy request
        req_domain_one = create_dummy_request(f"https://{domain_two}", "GET")

        # get the cookies for the request
        # this should return both cookies, since domain two is a subdomain of domain 1
        cookies_result = in_memory_sqlite_cookie_jar._cookies_for_request(req_domain_one)

        assert len(cookies_result) == 2
        assert_cookie_equality(cookies_result[0], test_cookie_one)
        assert_cookie_equality(cookies_result[1], test_cookie_two)

    def test_no_policy_two_cookies_different_domains(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests _cookies_for_request when you have multiple cookies
        but completely different domains
        '''

        domain_one = "example.com"
        domain_two = "zombo.com"


        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # create a dummy request
        req_domain_one = create_dummy_request(f"https://{domain_two}", "GET")

        # get the cookies for the request
        # this should return only 1 cookie since they are entirely different domains
        cookies_result = in_memory_sqlite_cookie_jar._cookies_for_request(req_domain_one)

        assert len(cookies_result) == 1
        assert_cookie_equality(cookies_result[0], test_cookie_two)

    def test_no_policy_two_cookies_dont_return_tld_cookies(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests _cookies_for_request when you have multiple cookies
        but one is a TLD (and the other is a first level domain / private suffix
        of that TLD)
        '''

        domain_one = "example.com"
        domain_two = "com"


        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_two = create_simple_cookie("c", "d", domain_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # create a dummy request
        req_domain_one = create_dummy_request(f"https://{domain_two}", "GET")

        # get the cookies for the request
        # this should return 0 cookies since we check to make sure the request is not
        # for a TLD, to avoid returning every cookie under that TLD
        cookies_result = in_memory_sqlite_cookie_jar._cookies_for_request(req_domain_one)

        assert len(cookies_result) == 0
