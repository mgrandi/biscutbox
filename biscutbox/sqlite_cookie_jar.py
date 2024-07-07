from contextlib import contextmanager
from http.cookiejar import CookieJar, CookiePolicy, Cookie
from os import PathLike
import email.message
import http
import json
import logging
import sqlite3
import typing
import urllib.request

from biscutbox import sql_statements as sql_statements

logger = logging.getLogger(__name__)

class SqliteCookieJar(CookieJar):
    '''
    a cookiejar that is backed by a SQLite database
    '''



    def __init__(self, database_path:PathLike, policy:CookiePolicy|None=None):
        '''
        constructor

        :param database_path: the path to an existing database, or where it should be stored.
        :param policy: the CookiePolicy object to use
        '''

        # call superclass
        super().__init__(policy)

        self.database_path:PathLike = database_path
        self.sqlite_connection:sqlite3.Connection|None = None

        if not database_path:
            raise ArgumentException(datab)

    @contextmanager
    def _get_sqlite3_database_cursor(self):

        with self.sqlite_connection:

            cur = None
            try:
                cur = self.sqlite_connection.cursor()
                yield cur
            except Exception as e:
                # do something with exception
                logger.exception("Uncaught exception in _get_sqlite3_database_cursor, performing rollback")
                self.sqlite_connection.rollback()
                raise
            else:
                logger.debug("sqlite3 database transaction committing")
                self.sqlite_connection.commit()
            finally:
                if cur:
                    logger.debug("sqlite3 cursor closing")
                    cur.close()

    def connect(self):
        '''
        connects to the database
        '''

        if not self.database_path:
            raise Exception("database_path cannot be None")

        logger.debug("Connecting to the sqlite database at the path `%s`", self.database_path)
        self.sqlite_connection = sqlite3.connect(database=self.database_path)
        self.sqlite_connection.row_factory = sqlite3.Row
        logger.info("Connected to the sqlite database at the path `%s`", self.database_path)

        self._create_tables()



    def _create_tables(self):
        '''
        create the sqlite3 tables if they don't already exist
        '''

        logger.debug("running create table statement")

        cursor = self.sqlite_connection.cursor()

        cursor.execute(sql_statements.CREATE_TABLE_STATEMENT_COOKIE_TABLE)

        cursor.close()

        logger.debug("create table statement finished")


    @typing.override
    def _cookies_for_domain(self, domain:str, request:urllib.request.Request) -> list[Cookie]:
        '''
        override of a private method , that returns the cookies for a given domain

        all overrides of private methods are fragile and are prone to breakage if the internals of http.cookiejar.CookeJar change


        :param domain: the domain to get the cookies from
        :param request: The request object (usually a urllib.request.Request instance) must support the method get_full_url()
        and the attributes host, unverifiable and origin_req_host, as documented by urllib.request. The request is used to set
        default values for cookie-attributes as well as for checking that the cookie is allowed to be set.
        :return: a list of Cookie objects that match this domain, or an empty list if the cookie policy rejects this domain
        (see CookiePolicy.domain_return_ok)

        '''
        pass


    @typing.override
    def set_cookie(self, cookie:Cookie):
        """Set a cookie, without checking whether or not it should be set.

        :param cookie: the Cookie object to add
        """

        self.set_cookies(cookie_list=[cookie])


    def set_cookies(self, cookie_list:list[Cookie]):
        '''
        non override method, but a way to bulk add cookies
        :param cookie_list: a sequence of Cookie objects to add
        '''

        with self._get_sqlite3_database_cursor() as cursor:

            logger.debug("inserting `%s cookies into the database", len(cookie_list))

            param_dict_list = list()

            for cookie in cookie_list:
                iter_param_dict = {
                    "version": cookie.version,
                    "name": cookie.name,
                    "value": cookie.value,
                    "port": cookie.port,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "secure": cookie.secure,
                    "expires": cookie.expires,
                    "discard": cookie.discard,
                    "comment": cookie.comment,
                    "comment_url": cookie.comment_url,
                    "rfc2109": cookie.rfc2109,
                    "rest": json.dumps(cookie._rest),
                    "port_specified": cookie.port_specified,
                    "domain_specified": cookie.domain_specified,
                    "domain_initial_dot": cookie.domain_initial_dot,
                    "path_specified": cookie.path_specified
                }

                param_dict_list.append(iter_param_dict)

            cursor.executemany(sql_statements.INSERT_COOKIE_STATEMENT, param_dict_list)


    @typing.override
    def _cookies_for_domain(self, domain, request):
        pass

    @typing.override
    def _cookies_for_request(self, request):
        pass

    @typing.override
    def clear(self, domain=None, path=None, name=None):
        pass

    @typing.override
    def clear_session_cookies(self):
        pass

    @typing.override
    def clear_expired_cookies(self):
        pass

    def __iter__(self):
        pass

    def __len__(self):
        '''
        __len__ implementation, this returns the number of contained cookies.
        For now, this invokes IO by queriyng the Sqlite database.
        :return: the number of contained cookies in this cookiejar
        '''
        pass

    def __repr__(self) -> str:
        '''__repr__ implementation, the original CookieJar implementation
        prints _every_ single cookie in the jar which doesn't scale, so far now we
        are just printing the naem

        :return: the string name of this class
        '''
        return f"<{self.__class__.__name__} />"

    def __str__(self):
        '''__str__ implementation, the original CookieJar implementation
        prints _every_ single cookie in the jar which doesn't scale, so far now we
        are just printing the naem

        :return: the string name of this class
        '''
        return f"<{self.__class__.__name__} />"
    def close(self):
        ''' commit and close the database'''

        logger.debug("Committing and closing connection")

        if self.sqlite_connection:
            self.sqlite_connection.commit()

            self.sqlite_connection.close()

            self.sqlite_connection = None




