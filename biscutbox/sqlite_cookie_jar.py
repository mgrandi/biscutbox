import sqlite3
import typing
from http.cookiejar import CookieJar, CookiePolicy, Cookie
from os import PathLike
import logging
import urllib.request
import email.message
import http

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

    def connect(self):
        '''
        connects to the database
        '''

        if not self.database_path:
            raise Exception("database_path cannot be None")

        logger.debug("Connecting to the sqlite database at the path `%s`", self.database_path)
        self.sqlite_connection = sqlite3.connect(database=self.database_path)
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

    def close(self):

        logger.debug("Committing and closing connection")

        if self.sqlite_connection:
            self.sqlite_connection.commit()

            self.sqlite_connection.close()

            self.sqlite_connection = None




