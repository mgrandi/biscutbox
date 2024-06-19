TABLE_NAME_V1 = "biscutbox_cookies_v1"

# a statement to create the Cookies V1 table
CREATE_TABLE_STATEMENT_COOKIE_TABLE = \
f'''CREATE TABLE IF NOT EXISTS "{TABLE_NAME_V1}"  (
    "id"    INTEGER NOT NULL,
    "version"   INTEGER NOT NULL,
    "name"  TEXT,
    "value" INTEGER,
    "port"  INTEGER,
    "domain"    TEXT NOT NULL,
    "path"  TEXT,
    "secure"    INTEGER,
    "expires"   INTEGER,
    "discard"   INTEGER,
    "comment"   INTEGER,
    "comment_url"   TEXT,
    "rfc2109"   INTEGER,
    "port_specified"    INTEGER,
    "domain_specified"  INTEGER,
    "domain_initial_dot"    INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT)
);
    '''