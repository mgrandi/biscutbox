from tests.fixtures import \
(
    database_path,
    sqlite_cookie_jar,
    giant_list_of_cookies,
    giant_cookiejar_jsonl_path
)
from biscutbox.sqlite_cookie_jar import SqliteCookieJar
from tests.test_utilities import assert_cookie_equality

import pathlib
import itertools
from http.cookiejar import Cookie

class TestSimple:

    def test_simple(self,
        sqlite_cookie_jar:SqliteCookieJar):

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


    def test_load_giant_cookie_file(
        self,
        sqlite_cookie_jar:SqliteCookieJar,
        giant_list_of_cookies:list[Cookie]):

        assert sqlite_cookie_jar != None

        assert giant_list_of_cookies != None

        for iter_batch in itertools.batched(giant_list_of_cookies, 20):

            sqlite_cookie_jar.set_cookies(iter_batch)

        assert sqlite_cookie_jar._policy != None


        assert len(sqlite_cookie_jar) >= 0

    def test_insert_rows_and_test_len(
        self,
        sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests to make sure len() works after creating a database
        inserting a few rows and then calling len()

        :param sqlite_cookie_jar: a sqlite cookie jar object created with a database
        saved to a temporary folder somewhere. provided by a fixture
        '''

        assert len(sqlite_cookie_jar) == 0

        for i in range(5):
            test_cookie = Cookie(
                version=0,
                name=f"a{i}",
                value=f"b{i}",
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

        assert len(sqlite_cookie_jar) == 5




    def test_insert_rows_and_test_iter(
        self,
        sqlite_cookie_jar:SqliteCookieJar):
        '''
        tests to see if iter() works after creating a database,
        inserting a few rows and then calling iter()
        :param sqlite_cookie_jar: a sqlite cookie jar object created with a database
        saved to a temporary folder somewhere. provided by a fixture
        '''


        #id,version,name,value,port,domain,path,secure,expires,discard,comment,comment_url,rfc2109,rest,port_specified,domain_specified,domain_initial_dot,path_specified
        # 22,0,ASP.NET_SessionId,cbhsgajr2x4fu03ez5xrozc0,,example.com,/,0,,1,,,0,"{""HttpOnly"": null, ""SameSite"": ""Lax""}",0,0,0,1
        cookie_one = Cookie(
            version=0,
            name=f"ASP.NET_SessionId",
            value=f"cbhsgajr2x4fu03ez5xrozc0",
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
            rest={"HttpOnly": None, "SameSite": "Lax"},
            rfc2109=False)

        #id,version,name,value,port,domain,path,secure,expires,discard,comment,comment_url,rfc2109,rest,port_specified,domain_specified,domain_initial_dot,path_specified
        #9204,0,wordpress_test_cookie,WP%20Cookie%20check,,nhadat24.org,/wp-content/themes/classipress/images,0,,1,,,0,{},0,0,0,0

        cookie_two = Cookie(
            version=0,
            name=f"ASP.wordpress_test_cookie",
            value=f"WP%20Cookie%20check",
            port=None,
            port_specified=False,
            domain="example.com",
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=False,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False)

        # assert it starts off as empty
        assert len(sqlite_cookie_jar) == 0

        # add the two cookies
        sqlite_cookie_jar.set_cookies([cookie_one, cookie_two])

        # assert count is now 2
        assert len(sqlite_cookie_jar) == 2

        # now test iter(), it SHOULD be in order, so cookie_one and then cookie_two
        iter_list = list(iter(sqlite_cookie_jar))

        assert len(iter_list) == 2
        assert_cookie_equality(iter_list[0], cookie_one)
        assert_cookie_equality(iter_list[1], cookie_two)


