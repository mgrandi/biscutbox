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


class TestClearSession():
    '''
    a class that will test clear_session_cookies
    '''

    def test_clear_session_cookies_simple(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        test clear_session_cookies with a simple test case
        '''

        domain_one = "example.com"
        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_one.discard = True
        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")

        assert test_cookie_one.discard == True

        ## assert jar is empty
        assert len(in_memory_sqlite_cookie_jar) == 0

        # insert cookie
        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one])

        # assert jar has 1 cookie
        assert len(in_memory_sqlite_cookie_jar) == 1

        # assert we can fetch the cookie we inserted
        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 1
        assert_cookie_equality(domain_one_result[0], test_cookie_one)

        # now clear the session cookies

        in_memory_sqlite_cookie_jar.clear_session_cookies()

        # assert cookie jar is empty
        assert len(in_memory_sqlite_cookie_jar) == 0

        # assert cookie is no longer present when we request cookies for that domain
        domain_one_result_after = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result_after) == 0

    def test_clear_session_cookies_multiple_cookies(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        test clear_session_cookies with two cookies
        '''

        domain_one = "example.com"
        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_one.discard = True
        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")

        domain_two = "a.example.com"
        test_cookie_two = create_simple_cookie("c", "d", domain_two)
        req_domain_two = create_dummy_request(f"https://{domain_two}", "GET")
        test_cookie_two.discard = False

        assert test_cookie_one.discard == True
        assert test_cookie_two.discard == False

        # assert jar is empty
        assert len(in_memory_sqlite_cookie_jar) == 0

        # insert cookies
        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert jar has 2 cookies
        assert len(in_memory_sqlite_cookie_jar) == 2

        # assert we can fetch the cookies we inserted
        domain_one_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result) == 1
        assert_cookie_equality(domain_one_result[0], test_cookie_one)

        domain_two_result = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result) == 1
        assert_cookie_equality(domain_two_result[0], test_cookie_two)

        # now clear the session cookies
        # this should clear the 'domain_one' cookie but not 'domain_two'

        in_memory_sqlite_cookie_jar.clear_session_cookies()

        # assert cookie jar size
        assert len(in_memory_sqlite_cookie_jar) == 1

        # assert cookie is no longer present when we request cookies for that domain
        domain_one_result_after = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result_after) == 0

        domain_two_result_after = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result_after) == 1
        assert_cookie_equality(domain_two_result_after[0], test_cookie_two)
