TABLE_NAME_V1 = "biscutbox_cookies_v1"

'''
a statement to create the Cookies V1 table
setting a basic cookie shows every value filled in except for:

value
port
expires
comment
comment_url

everything else i set as NOT NULL

>>> cj = http.cookiejar.CookieJar()
>>> opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
>>> urllib.request.install_opener(opener)
>>> x = urllib.request.urlopen("https://httpbin.org/cookies/set/a/b")
>>> cj
<CookieJar[Cookie(version=0, name='a', value='b', port=None, port_specified=False, domain='httpbin.org',
    domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None,
    discard=True, comment=None, comment_url=None, rest={}, rfc2109=False)]>
'''
CREATE_TABLE_STATEMENT_COOKIE_TABLE:str = \
f'''
CREATE TABLE IF NOT EXISTS "{TABLE_NAME_V1}"  (
    "id" INTEGER NOT NULL,
    "version" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "value" TEXT,
    "port" INTEGER ,
    "domain" TEXT NOT NULL,
    "path" TEXT NOT NULL,
    "secure" INTEGER NOT NULL,
    "expires" INTEGER,
    "discard" INTEGER NOT NULL,
    "comment" INTEGER,
    "comment_url" TEXT,
    "rfc2109" INTEGER NOT NULL,
    "rest" TEXT NOT NULL,
    "port_specified" INTEGER NOT NULL,
    "domain_specified" INTEGER NOT NULL,
    "domain_initial_dot" INTEGER NOT NULL,
    "path_specified" INTEGER NOT NULL,
    PRIMARY KEY("id" AUTOINCREMENT)
);
'''

CREATE_COOKIE_TABLE_DOMAIN_INDEX_STATEMENT:str = \
f'''
CREATE INDEX IF NOT EXISTS
"domain_idx" ON {TABLE_NAME_V1}
(
    "domain"
);
'''

'''
A SQL statement to insert a http.cookiejar into the database
'''
INSERT_COOKIE_STATEMENT:str = \
f'''
INSERT INTO "{TABLE_NAME_V1}"
(
    "version",
    "name",
    "value",
    "port",
    "domain",
    "path",
    "secure",
    "expires",
    "discard",
    "comment",
    "comment_url",
    "rfc2109",
    "rest",
    "port_specified",
    "domain_specified",
    "domain_initial_dot",
    "path_specified"
)
VALUES
(
    :version,
    :name,
    :value,
    :port,
    :domain,
    :path,
    :secure,
    :expires,
    :discard,
    :comment,
    :comment_url,
    :rfc2109,
    :rest,
    :port_specified,
    :domain_specified,
    :domain_initial_dot,
    :path_specified
);

'''

'''
the key to the value of the count() SQL statement
'''
COUNT_ENTRIES_IN_COOKIE_TABLE_KEY = "count_value"

'''
SQL statement that retrieves the number of rows modified by the most recent update/insert/delete
https://www.sqlite.org/c3ref/changes.html
https://www.sqlite.org/lang_corefunc.html#changes
'''
ROWS_MODIFIED:str = \
f'''
SELECT changes();
'''

'''
a SQL statement to count the number of entries in the
v1 cookies table
'''
COUNT_ENTRIES_IN_COOKIE_TABLE_STATEMENT:str = \
f'''
SELECT COUNT(id) AS {COUNT_ENTRIES_IN_COOKIE_TABLE_KEY} FROM "{TABLE_NAME_V1}";

'''

'''
the batch size for the select all sql statement
'''
SELECT_ALL_FROM_COOKIE_TABLE_BATCH_SIZE:int = 1000

'''
A SQL statement that is meant to iterate over the entire table
in batches. this has a python string.format marker `{}` that you are meant
to fill in, as you cannot use parameters in that spot.
'''
SELECT_ALL_FROM_COOKIE_TABLE_BATCH_STATEMENT:str = \
f'''
SELECT * FROM "{TABLE_NAME_V1}"
LIMIT 1000 OFFSET {{}}'''


'''
a SQL statement that will return all of the cookies that match the
given domain.
'''
SELECT_ALL_FROM_COOKIE_TABLE_DOMAIN_STATEMENT:str = \
f'''
SELECT * FROM "{TABLE_NAME_V1}"
WHERE domain == :domain
'''

'''
a SQL statement that will return all of the cookies that match the
given domain using sqlite LIKE
see https://sqlite.org/lang_expr.html#the_like_glob_regexp_match_and_extract_operators

'''
SELECT_ALL_FROM_COOKIE_TABLE_DOMAIN_LIKE_STATEMENT:str = \
f'''
SELECT * FROM "{TABLE_NAME_V1}"
WHERE domain LIKE :domain_pattern
'''

'''
SQL statement to turn foreign keys on
see https://www3.sqlite.org/quirks.html#foreign_key_enforcement_is_off_by_default
'''
TURN_FOREIGN_KEYS_ON:str = \
'''
PRAGMA foreign_keys = true;
'''

'''
SQL statement to turn Write Ahead Logging on
see https://www.sqlite.org/wal.html
'''
TURN_WAL_MODE_ON:str = \
f'''
PRAGMA journal_mode=WAL;
'''

'''
SQL statement to delete all cookies from the cookie table
'''
DELETE_ALL_FROM_COOKIE_TABLE:str = \
f'''
DELETE FROM "{TABLE_NAME_V1}"
'''

'''
SQL statement to delete all cookies from the cookie table
for a given domain
'''
DELETE_ALL_FROM_COOKIE_TABLE_BY_DOMAIN:str = \
f'''
DELETE FROM "{TABLE_NAME_V1}" WHERE domain == :domain
'''

'''
SQL statement to delete all session cookies from the cookie table
'''
DELETE_ALL_SESSION_COOKIES_FROM_COOKIE_TABLE:str = \
f'''
DELETE FROM "{TABLE_NAME_V1}" WHERE discard == 1
'''

'''
SQL statement to delete all expired cookies from the cookie table
'''
DELETE_ALL_EXPIRED_COOKIES_FROM_COOKIE_TABLE:str = \
f'''
DELETE FROM "{TABLE_NAME_V1}" WHERE (expires notnull AND expires <= :expires_val)
'''