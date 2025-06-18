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
import time
import itertools
from http.cookiejar import Cookie
import logging

logger = logging.getLogger(__name__)

class TestClearExpired():
    '''
    a class that will test clear_expired_cookies

    These use a override that takes a custom `now` value, as the method in http.cookiejar.CookieJar
    only uses the output of `time.time()` which you can't really unit test.
    '''

    def test_clear_expired_cookies_simple(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        test clear_expired_cookies with a simple test case
        '''

        # this has to be dynamic since _cookies_for_domain will not return expired cookies
        expiry_time = int(time.time()) + 100
        expiry_time_cookie_one = expiry_time - 50 # 50 seconds before cookie 2's expiraton
        expiry_time_cookie_two = expiry_time

        logger.debug("expiry time for cookie 1: `%s`, cookie 2: `%s`", expiry_time_cookie_one, expiry_time_cookie_two)

        domain_one = "example.com"
        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_one.expires = expiry_time_cookie_one
        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")

        # expires 10 seconds past expiry_time
        domain_two = "a.example.com"
        test_cookie_two = create_simple_cookie("c", "d", domain_two)
        req_domain_two = create_dummy_request(f"https://{domain_two}", "GET")
        test_cookie_two.expires = expiry_time_cookie_two

        assert test_cookie_one.expires == expiry_time_cookie_one
        assert test_cookie_two.expires == expiry_time_cookie_two
        # make sure that cookie 2's expiration date is greater than cookie 1's
        assert test_cookie_two.expires > test_cookie_one.expires

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

        # now remove expired cookies
        in_memory_sqlite_cookie_jar.clear_expired_cookies_from_time(expiry_time_cookie_one)

        # this should have cleared test_cookie_one, but not test_cookie_two
        # since cookie 1 has expiration of say, 11:59:50 but cookie 2 has expiration of 12:00:00
        assert len(in_memory_sqlite_cookie_jar) == 1

        domain_one_result_after1 = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result_after1) == 0

        domain_two_result_after1 = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result_after1) == 1
        assert_cookie_equality(domain_two_result_after1[0], test_cookie_two)

        # if we clear expired cookies and pass in `expiry_time` exactly, that should clear out the second cookie as well
        # since if cookie 1 has expiration of 11:59:50 and cookie two an expiration of 12:00:00
        # if we say 'delete all cookies that expire at 12:00:00' it should delete both cookies
        in_memory_sqlite_cookie_jar.clear_expired_cookies_from_time(expiry_time_cookie_two)

        assert len(in_memory_sqlite_cookie_jar) == 0

        domain_one_result_after2 = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(domain_one_result_after2) == 0

        domain_two_result_after2 = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_two, req_domain_two)
        assert len(domain_two_result_after2) == 0