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
from tests.cookie_policies import COOKIE_POLICY_ONLY_EXAMPLE_COM

from urllib.request import Request
import pathlib
import itertools
from http.cookiejar import Cookie, DefaultCookiePolicy


class TestCookiePolicy():



    def test_cookies_for_domain_simple(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):
        '''
        runs some basic tests with a CookiePolicy and the `_cookies_for_domain` method
        '''

        assert in_memory_sqlite_cookie_jar != None

        in_memory_sqlite_cookie_jar.set_policy(COOKIE_POLICY_ONLY_EXAMPLE_COM)

        policy_domain = "example.com"
        non_policy_domain = "contoso.com"
        test_cookie = Cookie(
            version=0,
            name="a",
            value="b",
            port=None,
            port_specified=False,
            domain=policy_domain,
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

        in_memory_sqlite_cookie_jar.set_cookie(test_cookie)

        test_cookie_two = Cookie(
            version=0,
            name="c",
            value="d",
            port=None,
            port_specified=False,
            domain=non_policy_domain,
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

        in_memory_sqlite_cookie_jar.set_cookie(test_cookie_two)

        # assert count is now 2
        assert len(in_memory_sqlite_cookie_jar) == 2

        request_for_policy_domain = create_dummy_request(f"https://{policy_domain}", "GET")
        request_for_nonpolicy_domain = create_dummy_request(f"https://{non_policy_domain}", "GET")

        # should be 0, as this domain is not in the policy
        cookie_list_not_in_policy = in_memory_sqlite_cookie_jar._cookies_for_domain(
            domain=non_policy_domain,request=request_for_nonpolicy_domain)

        assert len(cookie_list_not_in_policy) == 0

        # should be 1, as this domain is in the policy
        cookie_list_in_policy = in_memory_sqlite_cookie_jar._cookies_for_domain(
            domain=policy_domain, request=request_for_policy_domain)

        assert len(cookie_list_in_policy) == 1

        policy_cookie = cookie_list_in_policy[0]
        assert policy_cookie.name == "a"
        assert policy_cookie.value == "b"
        assert policy_cookie.domain == policy_domain

        #####################################
        # set the policy to DefaultCookiePolicy and then try again
        ####################################
        in_memory_sqlite_cookie_jar.set_policy(DefaultCookiePolicy() )

        # should be 0 normally, as this domain is not in the policy
        # but will be 1 because we have the null policy
        cookie_list_not_in_policy2 = in_memory_sqlite_cookie_jar._cookies_for_domain(
            domain=non_policy_domain,request=request_for_nonpolicy_domain)
        assert len(cookie_list_not_in_policy2) == 1
        not_policy_cookie = cookie_list_not_in_policy2[0]
        assert not_policy_cookie.name == "c"
        assert not_policy_cookie.value == "d"
        assert not_policy_cookie.domain == non_policy_domain


        # should be 1, as this domain is in the policy
        # and we have the null policy attached
        cookie_list_in_policy2 = in_memory_sqlite_cookie_jar._cookies_for_domain(
            domain=policy_domain, request=request_for_policy_domain)

        assert len(cookie_list_in_policy2) == 1
        policy_cookie2 = cookie_list_in_policy2[0]
        assert policy_cookie2.name == "a"
        assert policy_cookie2.value == "b"
        assert policy_cookie2.domain == policy_domain