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
from tests.testing_util import \
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


    def test_clear_two_arguments_domain_path_provided(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):

        domain_one = "example.com"
        path_one = "/"
        path_two = "/foo/bar"

        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_one.path = path_one
        test_cookie_two = create_simple_cookie("c", "d", domain_one)
        test_cookie_two.path = path_two

        assert test_cookie_one.path == path_one
        assert test_cookie_two.path == path_two

        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")
        req_domain_two = create_dummy_request(f"https://{domain_one}{path_two}", "GET")

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 2

        # assert cookie is there with path `/`
        pre_result_zero = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(pre_result_zero) == 1
        assert_cookie_equality(pre_result_zero[0], test_cookie_one)

        # assert cookie is there with path `/foo/bar`
        # this will return both cookies, since the cookie policy will consider paths as valid if
        # one path is a subset of another, so since `/` is a valid subpath of `/foo/bar`, the
        # first cookie with the path `/` will be returned when we have a request for `/foo/bar`
        #
        # i sort the results by path here to make assertions deterministic
        pre_result_one = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(pre_result_one) == 2
        pre_result_one_sorted = sorted(pre_result_one, key=lambda x: x.path)
        assert_cookie_equality(pre_result_one_sorted[0], test_cookie_one)
        assert_cookie_equality(pre_result_one_sorted[1], test_cookie_two)

        # clear the cookie jar for one domain / path
        in_memory_sqlite_cookie_jar.clear(
            domain=domain_one,
            path=path_one)

        # assert we only have 1 left
        assert len(in_memory_sqlite_cookie_jar) == 1

        # first cookie, under the path `/` should be gone
        result_zero = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(result_zero) == 0

        # second cookie should still exist under /foo/bar path and request
        result_one = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(result_one) == 1
        assert_cookie_equality(result_one[0], test_cookie_two)

        # clear the second cookie by the second path
        in_memory_sqlite_cookie_jar.clear(
            domain=domain_one,
            path=path_two)

        # cookie with path `/` should be gone
        result_two = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(result_two) == 0

        # cookie with path `/foo/bar/` should be gone
        result_three = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(result_three) == 0

    def test_clear_three_arguments_domain_path_name_provided(
        self,
        in_memory_sqlite_cookie_jar:SqliteCookieJar):

        domain_one = "example.com"
        path_one = "/"
        path_two = "/foo/bar"

        test_cookie_one = create_simple_cookie("a", "b", domain_one)
        test_cookie_one.path = path_one
        test_cookie_two = create_simple_cookie("c", "d", domain_one)
        test_cookie_two.path = path_two
        # same as cookie 2 but name is different
        test_cookie_three = create_simple_cookie("e", "f", domain_one)
        test_cookie_three.path = path_two

        assert test_cookie_one.path == path_one
        assert test_cookie_two.path == path_two
        assert test_cookie_three.path == path_two

        req_domain_one = create_dummy_request(f"https://{domain_one}", "GET")
        req_domain_two = create_dummy_request(f"https://{domain_one}{path_two}", "GET")

        assert len(in_memory_sqlite_cookie_jar) == 0

        in_memory_sqlite_cookie_jar.set_cookies([test_cookie_one, test_cookie_two, test_cookie_three])

        # assert there are two cookies in the cookie jar
        assert len(in_memory_sqlite_cookie_jar) == 3

        # assert cookie is there with path `/`
        pre_result_zero = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(pre_result_zero) == 1
        assert_cookie_equality(pre_result_zero[0], test_cookie_one)

        # assert cookie is there with path `/foo/bar`
        # this will return all cookies, since the cookie policy will consider paths as valid if
        # one path is a subset of another, so since `/` is a valid subpath of `/foo/bar`, the
        # first cookie with the path `/` will be returned when we have a request for `/foo/bar`
        #
        # i sort the results by path here to make assertions deterministic
        pre_result_one = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(pre_result_one) == 3
        pre_result_one_sorted = sorted(pre_result_one, key=lambda x: x.path + x.name)
        assert_cookie_equality(pre_result_one_sorted[0], test_cookie_one)
        assert_cookie_equality(pre_result_one_sorted[1], test_cookie_two)
        assert_cookie_equality(pre_result_one_sorted[2], test_cookie_three)


        # clear the cookie jar for one domain / path
        in_memory_sqlite_cookie_jar.clear(
            domain=domain_one,
            path=path_one)

        # assert we only have 2 left
        assert len(in_memory_sqlite_cookie_jar) == 2

        # first cookie, under the path `/` should be gone
        result_zero = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(result_zero) == 0

        # second/third cookie should still exist under /foo/bar path and request
        result_one = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(result_one) == 2
        post_result_one_sorted = sorted(result_one, key=lambda x: x.path + x.name)
        assert_cookie_equality(post_result_one_sorted[0], test_cookie_two)
        assert_cookie_equality(post_result_one_sorted[1], test_cookie_three)


        # clear the second cookie by the second path and the name
        in_memory_sqlite_cookie_jar.clear(
            domain=domain_one,
            path=path_two,
            name="c")

        # cookie with path `/` should be gone
        result_two = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_one)
        assert len(result_two) == 0

        # cookie with path `/foo/bar/` and name `c` should be gone
        result_three = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(result_three) == 1
        assert_cookie_equality(result_three[0], test_cookie_three)

        # clear the cookie with the same domain and path but now the final name
        in_memory_sqlite_cookie_jar.clear(
            domain=domain_one,
            path=path_two,
            name="e")

        # all cookies from that domain and path should be gone now
        result_four = in_memory_sqlite_cookie_jar._cookies_for_domain(domain_one, req_domain_two)
        assert len(result_four) == 0
