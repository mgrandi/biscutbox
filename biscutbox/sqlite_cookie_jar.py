from contextlib import contextmanager
from http.cookiejar import CookieJar, CookiePolicy, Cookie, request_host
from os import PathLike
import email.message
import http
import json
import logging
import sqlite3
import time
import typing
import urllib.request

import publicsuffixlist
from biscutbox import sql_statements as sql_statements

logger = logging.getLogger(__name__)

class SqliteCookieJar(CookieJar):
    '''
    a cookiejar that is backed by a SQLite database
    '''

    def __init__(self, database_path:PathLike, policy:CookiePolicy|None=None):
        '''
        constructor

        :param database_path: the path to an existing database, or where it should be stored. This is a PathLike
        so it can either be a pathlib.Path like object, or a string. Also, `:memory:` can be passed to
        use a in memory sqlite database.
        :param policy: the CookiePolicy object to use
        '''

        # call superclass
        super().__init__(policy)

        self._public_suffix_list = publicsuffixlist.PublicSuffixList()

        # python's cookiejar / cookie policy implementation is just updating this class instance variable _now
        # in various spots to check for expiry, rather than you know just using `time.time()`, and now
        # we have to worry about keeping these in sync?
        # so update it here for now
        self._now:int = int(time.time())
        self._policy._now = self._now

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

    def _get_changed_rows(self, cursor:sqlite3.Cursor) -> int:
        '''
        get the number of changed rows
        :param cursor: the cursor from an existing transaction
        :returns: the number of changed rows according to sqlite
        '''

        cursor.execute(sql_statements.ROWS_MODIFIED)
        changed_rows_result = cursor.fetchone()
        return changed_rows_result["changes()"]

    def connect(self):
        '''
        connects to the database
        '''

        if not self.database_path:
            raise Exception("database_path cannot be None")

        logger.debug("Connecting to the sqlite database at the path `%s`", self.database_path)
        self.sqlite_connection = sqlite3.connect(database=self.database_path)
        self.sqlite_connection.row_factory = sqlite3.Row

        # turn on foreign keys and WAL
        with self._get_sqlite3_database_cursor() as cur:
            cur.execute(sql_statements.TURN_FOREIGN_KEYS_ON)
            cur.execute(sql_statements.TURN_WAL_MODE_ON)
            wal_result = cur.fetchone()

            wal_result_key = "journal_mode"
            if wal_result_key in wal_result.keys():
                logger.debug("WAL pragma result: `%s`", wal_result[wal_result_key])
            else:
                logger.warning("couldn't find the key `%s` in the sqlite3.Row object returned after `%s`",
                    wal_result_key, sql_statements.TURN_WAL_MODE_ON)

        logger.info("Connected to the sqlite database at the path `%s`", self.database_path)

        self._create_tables()



    def _create_tables(self):
        '''
        create the sqlite3 tables if they don't already exist
        '''

        logger.debug("running create table statement")

        with self._get_sqlite3_database_cursor() as cursor:

            # create tables
            cursor.execute(sql_statements.CREATE_TABLE_STATEMENT_COOKIE_TABLE)

            # create indexes
            cursor.execute(sql_statements.CREATE_COOKIE_TABLE_DOMAIN_INDEX_STATEMENT)

        logger.debug("create table statement finished")


    @typing.override
    def _cookies_for_domain(self, domain:str, request:urllib.request.Request) -> list[Cookie]:
        '''
        override of a private method , that returns the cookies for a given domain

        all overrides of private methods are fragile and are prone to breakage if the internals of http.cookiejar.CookeJar change

        this performs database I/O by looking up cookies for the given domain

        :param domain: the domain to get the cookies from
        :param request: The request object (usually a urllib.request.Request instance) must support the method get_full_url()
        and the attributes host, unverifiable and origin_req_host, as documented by urllib.request. The request is used to set
        default values for cookie-attributes as well as for checking that the cookie is allowed to be set.
        :return: a list of Cookie objects that match this domain, or an empty list if the cookie policy rejects this domain
        (see CookiePolicy.domain_return_ok)

        '''

        # update the semi global 'now' variable to check for expiry
        self._policy._now = self._now = int(time.time())


        # check the policy first
        if not self._policy.domain_return_ok(domain, request):
            return list()

        logger.debug("Checking the domain `%s` for cookies to return", domain)

        result_list = list()

        # make the database query for all cookies under this domain, then we will filter them
        # out based on the policies
        with self._get_sqlite3_database_cursor() as cursor:

            param_dict = {"domain": domain}
            cursor.execute(
                sql_statements.SELECT_ALL_FROM_COOKIE_TABLE_DOMAIN_STATEMENT,
                param_dict)

            while (iter_row := cursor.fetchone()) != None:

                tmp_cookie = self._cookie_from_sqlite_row(iter_row)

                # check the cookie policy and if both pass, add it to the result list
                # the default policy will call `path_return_ok` which checks the full URL on the `request` parameter
                # and 'return_ok" checks `return_ok_port`, `return_ok_verifiability`, `return_ok_secure`,
                # `return_ok_expires`, `return_ok_domain`, `return_ok_version`
                if (self._policy.path_return_ok(tmp_cookie.path, request)
                    and self._policy.return_ok(tmp_cookie, request)):

                    result_list.append(tmp_cookie)
                else:
                    logger.debug("cookie with name `%s` failed one or both of the policy checks, not returning",
                        tmp_cookie.name)

        logger.debug("returning `%s` cookies", len(result_list))

        return result_list

    @typing.override
    def _cookies_for_request(self, request:urllib.request.Request) -> list[Cookie]:
        '''
        override of a private method , that returns the cookies for a given domain

        all overrides of private methods are fragile and are prone to breakage if the internals of http.cookiejar.CookeJar change

        this performs database I/O by looking up cookies for the given domain

        this will return a list of cookies to return for a given request

        :param request: the Request that we want the cookies for
        :return: a list of Cookie objects

        '''


        # so, the original implementation of this seems to just iterate over the cookies dictionary
        # and then call `_cookies_for_domain` on each domain. That is incredibly slow, however this is accurate
        # since there are various cookie rules around cookies and domains, like a cookie for domain
        # `.twitter.com` versus `twitter.com` versus `a.twitter.com`.
        # here, we are utilizing the index on the cookie table and using the sqlite LIKE operator to
        # get cookies for all domains that contain the request domain, and then we will pass those to `_cookies_for_domain`
        # to do the fine grained filtering.


        # get all the cookies that match the glob of the "private suffix", aka
        # the lowest level domain that a user can register
        # this is extremely complicated so we use a library for this, see https://publicsuffix.org
        # a.example.com -> private suffix is example.com
        # a.example.co.uk -> private suffix is example.co.uk
        # we also need to check to make sure that we aren't returning cookies for top level domains
        # as that is bad form

        hostname = request_host(request)
        private_suffix = self._public_suffix_list.privatesuffix(hostname)

        if not private_suffix or self._public_suffix_list.is_public(private_suffix):
            # either invalid or a public suffix (like `com`) which means we we don't want to return anything
            # (don't want websites setting a cookie for a TLD and having it be sent to every website under
            # that TLD)

            logger.debug("for the hostname `%s`, the private suffix `%s` is either None or a public suffix, returning empty list",
                hostname, private_suffix)

            return list()

        result_list = list()


        # make the database query for all cookies under this domain, then we will filter them
        # out based on the policies
        with self._get_sqlite3_database_cursor() as cursor:

            search_term = f"%{private_suffix}"

            logger.debug("_cookie_for_request with full url `%s`, searching for cookies with the glob `%s`",
                hostname, search_term)

            param_dict = {"domain_pattern": search_term}

            cursor.execute(
                sql_statements.SELECT_ALL_FROM_COOKIE_TABLE_DOMAIN_LIKE_STATEMENT,
                param_dict)


            while (iter_row := cursor.fetchone()) != None:

                tmp_cookie = self._cookie_from_sqlite_row(iter_row)

                # check the cookie policy and if both pass, add it to the result list
                # the default policy will call `path_return_ok` which checks the full URL on the `request` parameter
                # and 'return_ok" checks `return_ok_port`, `return_ok_verifiability`, `return_ok_secure`,
                # `return_ok_expires`, `return_ok_domain`, `return_ok_version`
                if (self._policy.path_return_ok(tmp_cookie.path, request)
                    and self._policy.return_ok(tmp_cookie, request)):

                    result_list.append(tmp_cookie)
                else:
                    logger.debug("cookie with name `%s` failed one or both of the policy checks, not returning",
                        tmp_cookie.name)

        return result_list


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
    def clear(self, domain=None, path=None, name=None):
        '''
        Clear some cookies.

        If invoked without arguments, clear all cookies. If given a single argument,
        only cookies belonging to that domain will be removed. If given two arguments,
        cookies belonging to the specified domain and URL path are removed.
        If given three arguments, then the cookie with the specified domain, path and name is removed.

        Raises KeyError if no matching cookie exists.

        Mark note: this api intereface is worded weird, you need domain, domain + path, domain + path + name
        https://github.com/python/cpython/blob/fb8bb36f56e4fc2948cd404337b6b316b78c86aa/Lib/http/cookiejar.py#L1692
        '''

        # copied the if...elif.. else structure from python3 cookiejar.py
        if name is not None:
            if (domain is None) or (path is None):
                raise ValueError(
                    "domain and path must be given to remove a cookie by name")
            self._clear_cookies_given_domain_path_and_name(domain=domain, path=path, name=name)
            return

        elif path is not None:
            if domain is None:
                raise ValueError(
                    "domain must be given to remove cookies by path")
            self._clear_cookies_given_domain_and_path(domain=domain, path=path)
            return

        elif domain is not None:
            self._clear_cookies_given_domain(domain=domain)
            return

        else:
            # no arguments, clear all cookies
            self._clear_all_cookies()
            return

    @typing.override
    def clear_session_cookies(self) -> None:
        '''
        Discard all session cookies.

        Discards all contained cookies that have a true discard attribute (usually because they had either
        no max-age or expires cookie-attribute, or an explicit discard cookie-attribute).
        For interactive browsers, the end of a session usually corresponds to closing the browser window.

        Note that the save() method won’t save session cookies anyway, unless you ask otherwise by passing a
        true ignore_discard argument
        '''

        with self._get_sqlite3_database_cursor() as cursor:
            logger.debug("Removing all session cookies")

            cursor.execute(sql_statements.DELETE_ALL_SESSION_COOKIES_FROM_COOKIE_TABLE)

            changed_rows = self._get_changed_rows(cursor)

            logger.debug("deletion of session cookies complete, deleted `%s` cookies", changed_rows)


    def clear_expired_cookies_from_time(self, expires_time:int) -> None:
        '''
        Discard all expired cookies, where `cookie.expires` is not null and whose `expires` value is
        less than the passed in parameter :expires_time:

        :param expires_time: the time to compare the cookie's `expires` time with when deciding what cookie to clear out
        '''


        with self._get_sqlite3_database_cursor() as cursor:
            logger.debug("Removing all expired cookies from the database whose expiry is older than `%s`", expires_time)

            param_dict = {"expires_val": expires_time}

            cursor.execute(sql_statements.DELETE_ALL_EXPIRED_COOKIES_FROM_COOKIE_TABLE, param_dict)

            changed_rows = self._get_changed_rows(cursor)

            logger.debug("deletion of expired cookies completed, deleted `%s` cookies", changed_rows)


    @typing.override
    def clear_expired_cookies(self) -> None:
        '''
        Discard all expired cookies (where `cookie.expires` is not null and whose value is less than the current date)

        Note: this diverges heavily from the base cookiejar implementation. The base implementation iterates over
        every cookie in the cookie jar, and asks each cookie "if it is expired" and if true, it will remove it

        But obviously this is extremely not scalable if the cookiejar is huge, as it will have to do a O(N) number of
        checks.

        the implementation of `cookie.is_expired(time)` is basically
        if (expired != None && expired <= now)
            return True
        return False

        so we can just implement this using a sqlite statement and have this be much more performant with huge
        cookie jars
        '''


        # just call the 'new' method we created (for unit tests) with `time.time()`
        # the expires attribute appears to be an unix timestamp, seconds since the epoch. `time.time()` returns
        # a floating point number but the parsing seems to only care about whole seconds
        expires_time_val = int(time.time())
        self.clear_expired_cookies_from_time(expires_time=expires_time_val)


    def _clear_cookies_given_domain_path_and_name(self, domain:str, path:str, name:str) -> None:

        pass

    def _clear_cookies_given_domain_and_path(self, domain:str, path:str) -> None:

        pass

    def _clear_cookies_given_domain(self, domain:str):
        '''
        clear cookies under a specific domain
        :param domain: the domain whose cookies we want to clear

        Note: this is for a specific domain, using string equality. The actual method
        uses dictionary syntax. So calling this method with `example.com` will not delete
        cookies for `a.example.com`
        '''

        if domain is None:
            raise Exception("`domain` should not be None")

        with self._get_sqlite3_database_cursor() as cursor:
            logger.debug("Removing all cookies from the database that match domain `%s`", domain)
            param_dict = {"domain": domain}
            cursor.execute(sql_statements.DELETE_ALL_FROM_COOKIE_TABLE_BY_DOMAIN, param_dict)

            logger.debug("deletion of cookies complete")


    def _clear_all_cookies(self):
        '''
        delete all cookies
        '''

        with self._get_sqlite3_database_cursor() as cursor:

            logger.debug("removing all cookies from the database")

            cursor.execute(sql_statements.DELETE_ALL_FROM_COOKIE_TABLE)

            logger.debug("deletion of all cookies completed")

    def __iter__(self):
        '''
        __iter__ implementation, this will iterate over the entire database in batchces.
        This performs IO on the database, by selecting the total number of rows and then
        fetching them in batches one by one.
        '''

        # get number of rows
        number_of_rows = len(self)

        logger.debug("__iter__: number of rows are `%s`", number_of_rows)
        with self._get_sqlite3_database_cursor() as cursor:

            # get count of rows in database
            number_of_rows = len(self)

            for iter_offset in range(0, number_of_rows, sql_statements.SELECT_ALL_FROM_COOKIE_TABLE_BATCH_SIZE):

                # format the sql statement
                iter_select_all_statement = sql_statements.SELECT_ALL_FROM_COOKIE_TABLE_BATCH_STATEMENT.format(iter_offset)

                logger.debug("executing 'select all batch' statement with offset `%s`", iter_offset)

                # execute it
                cursor.execute(iter_select_all_statement)
                iter_result = cursor.fetchall()

                for iter_row in iter_result:

                    # now yield one by one
                    iter_cookie = self._cookie_from_sqlite_row(iter_row)
                    yield iter_cookie

    def _cookie_from_sqlite_row(self, row:sqlite3.Row) -> Cookie:
        '''
        returns a cookie from a sqlite3 row

        :param row: the sqlite3.Row object we get from the database
        :return: the Cookie object we parsed
        '''

        result_cookie = Cookie(
            version=row["version"],
            name=row["name"],
            value=row["value"],
            port=row["port"],
            port_specified=bool(row["port_specified"]),
            domain=row["domain"],
            domain_specified=bool(row["domain_specified"]),
            domain_initial_dot=bool(row["domain_initial_dot"]),
            path=row["path"],
            path_specified=bool(row["path_specified"]),
            secure=bool(row["secure"]),
            expires=row["expires"],
            discard=bool(row["discard"]),
            comment=row["comment"],
            comment_url=row["comment_url"],
            rest=json.loads(row["rest"]) if row["rest"] else {},
            rfc2109=bool(row["rfc2109"]))

        return result_cookie

    def __len__(self):
        '''
        __len__ implementation, this returns the number of contained cookies.
        For now, this invokes IO by queriyng the Sqlite database.
        :return: the number of contained cookies in this cookiejar
        '''
        with self._get_sqlite3_database_cursor() as cursor:
            cursor.execute(sql_statements.COUNT_ENTRIES_IN_COOKIE_TABLE_STATEMENT)
            fetch_result = cursor.fetchone()
            return fetch_result[sql_statements.COUNT_ENTRIES_IN_COOKIE_TABLE_KEY]


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




