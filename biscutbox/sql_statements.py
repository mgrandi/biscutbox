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
a SQL statement to count the number of entries in the
v1 cookies table
'''
COUNT_ENTRIES_IN_COOKIE_TABLE_STATEMENT:str = \
f'''
SELECT COUNT(id) AS {COUNT_ENTRIES_IN_COOKIE_TABLE_KEY} FROM "{TABLE_NAME_V1}";

'''