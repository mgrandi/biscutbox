import pytest

import os
import stat
import sys
import re
from test import support
from test.support import os_helper
from test.support import warnings_helper
import time
import unittest
import urllib.request
from http.cookiejar import (time2isoz, http2time, iso2time, time2netscape,
     parse_ns_headers, join_header_words, split_header_words, Cookie,
     CookieJar, DefaultCookiePolicy, LWPCookieJar, MozillaCookieJar,
     LoadError, lwp_cookie_str, DEFAULT_HTTP_PORT, escape_path,
     reach, is_HDN, domain_match, user_domain_match, request_path,
     request_port, request_host)

from biscutbox.sqlite_cookie_jar import SqliteCookieJar

mswindows = (sys.platform == "win32")

# Taken and slightly edited from
# https://github.com/python/cpython/blob/dd079db4b96fa474b8e6d71ae9db662c4ce28caf/Lib/test/test_http_cookiejar.py#
# https://github.com/python/cpython
# latest git commit: dd079db4b96fa474b8e6d71ae9db662c4ce28caf


class FakeResponse:
    def __init__(self, headers=[], url=None):
        """
        headers: list of RFC822-style 'Key: value' strings
        """
        import email
        self._headers = email.message_from_string("\n".join(headers))
        self._url = url
    def info(self): return self._headers

def interact_2965(cookiejar, url, *set_cookie_hdrs):
    return _interact(cookiejar, url, set_cookie_hdrs, "Set-Cookie2")

def interact_netscape(cookiejar, url, *set_cookie_hdrs):
    return _interact(cookiejar, url, set_cookie_hdrs, "Set-Cookie")

def _interact(cookiejar, url, set_cookie_hdrs, hdr_name):
    """Perform a single request / response cycle, returning Cookie: header."""
    req = urllib.request.Request(url)
    cookiejar.add_cookie_header(req)
    cookie_hdr = req.get_header("Cookie", "")
    headers = []
    for hdr in set_cookie_hdrs:
        headers.append("%s: %s" % (hdr_name, hdr))
    res = FakeResponse(headers, url)
    cookiejar.extract_cookies(res, req)
    return cookie_hdr

class TestCookieTestsWithSubTests():

    @pytest.mark.parametrize('url,domain,ok', [
        ("http://foo.bar.com/", "blah.com", False),
        ("http://foo.bar.com/", "rhubarb.blah.com", False),
        ("http://foo.bar.com/", "rhubarb.foo.bar.com", False),
        ("http://foo.bar.com/", ".foo.bar.com", True),
        ("http://foo.bar.com/", "foo.bar.com", True),
        ("http://foo.bar.com/", ".bar.com", True),
        ("http://foo.bar.com/", "bar.com", True),
        ("http://foo.bar.com/", "com", True),
        ("http://foo.com/", "rhubarb.foo.com", False),
        ("http://foo.com/", ".foo.com", True),
        ("http://foo.com/", "foo.com", True),
        ("http://foo.com/", "com", True),
        ("http://foo/", "rhubarb.foo", False),
        ("http://foo/", ".foo", True),
        ("http://foo/", "foo", True),
        ("http://foo/", "foo.local", True),
        ("http://foo/", ".local", True),
        ("http://barfoo.com", ".foo.com", False),
        ("http://barfoo.com", "foo.com", False),
    ])
    def test_domain_return_ok(self, url, domain, ok):
        # test optimization: .domain_return_ok() should filter out most
        # domains in the CookieJar before we try to access them (because that
        # may require disk access -- in particular, with MSIECookieJar)
        # This is only a rough check for performance reasons, so it's not too
        # critical as long as it's sufficiently liberal.
        pol = DefaultCookiePolicy()
        request = urllib.request.Request(url)
        r = pol.domain_return_ok(domain, request)
        if ok: assert r == True
        else: assert r == False

    @pytest.mark.parametrize('arg,result', [
            # quoted safe
            ("/foo%2f/bar", "/foo%2F/bar"),
            ("/foo%2F/bar", "/foo%2F/bar"),
            # quoted %
            ("/foo%%/bar", "/foo%%/bar"),
            # quoted unsafe
            ("/fo%19o/bar", "/fo%19o/bar"),
            ("/fo%7do/bar", "/fo%7Do/bar"),
            # unquoted safe
            ("/foo/bar&", "/foo/bar&"),
            ("/foo//bar", "/foo//bar"),
            ("\176/foo/bar", "\176/foo/bar"),
            # unquoted unsafe
            ("/foo\031/bar", "/foo%19/bar"),
            ("/\175foo/bar", "/%7Dfoo/bar"),
            # unicode, latin-1 range
            ("/foo/bar\u00fc", "/foo/bar%C3%BC"),     # UTF-8 encoded
            # unicode
            ("/foo/bar\uabcd", "/foo/bar%EA%AF%8D"),  # UTF-8 encoded
        ])
    def test_escape_path(self, arg, result):
        assert escape_path(arg) ==  result

    @pytest.mark.parametrize('rfc2109_as_netscape,rfc2965,version', [
            # default according to rfc2965 if not explicitly specified
            (None, False, 0),
            (None, True, 1),
            # explicit rfc2109_as_netscape
            (False, False, None),  # version None here means no cookie stored
            (False, True, 1),
            (True, False, 0),
            (True, True, 0),
        ])
    def test_rfc2109_handling(self, rfc2109_as_netscape, rfc2965, version):
        # RFC 2109 cookies are handled as RFC 2965 or Netscape cookies,
        # dependent on policy settings
        policy = DefaultCookiePolicy(
            rfc2109_as_netscape=rfc2109_as_netscape,
            rfc2965=rfc2965)
        c = CookieJar(policy)
        interact_netscape(c, "http://www.example.com/", "ni=ni; Version=1")
        try:
            cookie = c._cookies["www.example.com"]["/"]["ni"]
        except KeyError:
            assert version == None  # didn't expect a stored cookie
        else:
            assert cookie.version ==  version
            # 2965 cookies are unaffected
            interact_2965(c, "http://www.example.com/",
                            "foo=bar; Version=1")
            if rfc2965:
                cookie2965 = c._cookies["www.example.com"]["/"]["foo"]
                assert cookie2965.version ==  1


class CookieTests(unittest.TestCase):
    # XXX
    # Get rid of string comparisons where not actually testing str / repr.
    # .clear() etc.
    # IP addresses like 50 (single number, no dot) and domain-matching
    #  functions (and is_HDN)?  See draft RFC 2965 errata.
    # Strictness switches
    # is_third_party()
    # unverifiability / third-party blocking
    # Netscape cookies work the same as RFC 2965 with regard to port.
    # Set-Cookie with negative max age.
    # If turn RFC 2965 handling off, Set-Cookie2 cookies should not clobber
    #  Set-Cookie cookies.
    # Cookie2 should be sent if *any* cookies are not V1 (ie. V0 OR V2 etc.).
    # Cookies (V1 and V0) with no expiry date should be set to be discarded.
    # RFC 2965 Quoting:
    #  Should accept unquoted cookie-attribute values?  check errata draft.
    #   Which are required on the way in and out?
    #  Should always return quoted cookie-attribute values?
    # Proper testing of when RFC 2965 clobbers Netscape (waiting for errata).
    # Path-match on return (same for V0 and V1).
    # RFC 2965 acceptance and returning rules
    #  Set-Cookie2 without version attribute is rejected.

    # Netscape peculiarities list from Ronald Tschalar.
    # The first two still need tests, the rest are covered.
## - Quoting: only quotes around the expires value are recognized as such
##   (and yes, some folks quote the expires value); quotes around any other
##   value are treated as part of the value.
## - White space: white space around names and values is ignored
## - Default path: if no path parameter is given, the path defaults to the
##   path in the request-uri up to, but not including, the last '/'. Note
##   that this is entirely different from what the spec says.
## - Commas and other delimiters: Netscape just parses until the next ';'.
##   This means it will allow commas etc inside values (and yes, both
##   commas and equals are commonly appear in the cookie value). This also
##   means that if you fold multiple Set-Cookie header fields into one,
##   comma-separated list, it'll be a headache to parse (at least my head
##   starts hurting every time I think of that code).
## - Expires: You'll get all sorts of date formats in the expires,
##   including empty expires attributes ("expires="). Be as flexible as you
##   can, and certainly don't expect the weekday to be there; if you can't
##   parse it, just ignore it and pretend it's a session cookie.
## - Domain-matching: Netscape uses the 2-dot rule for _all_ domains, not
##   just the 7 special TLD's listed in their spec. And folks rely on
##   that...




    def test_ns_parser(self):
        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/",
                          'spam=eggs; DoMain=.acme.com; port; blArgh="feep"')
        interact_netscape(c, "http://www.acme.com/", 'ni=ni; port=80,8080')
        interact_netscape(c, "http://www.acme.com:80/", 'nini=ni')
        interact_netscape(c, "http://www.acme.com:80/", 'foo=bar; expires=')
        interact_netscape(c, "http://www.acme.com:80/", 'spam=eggs; '
                          'expires="Foo Bar 25 33:22:11 3022"')
        interact_netscape(c, 'http://www.acme.com/', 'fortytwo=')
        interact_netscape(c, 'http://www.acme.com/', '=unladenswallow')
        interact_netscape(c, 'http://www.acme.com/', 'holyhandgrenade')

        cookie = c._cookies[".acme.com"]["/"]["spam"]
        self.assertEqual(cookie.domain, ".acme.com")
        self.assertTrue(cookie.domain_specified)
        self.assertEqual(cookie.port, DEFAULT_HTTP_PORT)
        self.assertFalse(cookie.port_specified)
        # case is preserved
        self.assertTrue(cookie.has_nonstandard_attr("blArgh"))
        self.assertFalse(cookie.has_nonstandard_attr("blargh"))

        cookie = c._cookies["www.acme.com"]["/"]["ni"]
        self.assertEqual(cookie.domain, "www.acme.com")
        self.assertFalse(cookie.domain_specified)
        self.assertEqual(cookie.port, "80,8080")
        self.assertTrue(cookie.port_specified)

        cookie = c._cookies["www.acme.com"]["/"]["nini"]
        self.assertIsNone(cookie.port)
        self.assertFalse(cookie.port_specified)

        # invalid expires should not cause cookie to be dropped
        foo = c._cookies["www.acme.com"]["/"]["foo"]
        spam = c._cookies["www.acme.com"]["/"]["foo"]
        self.assertIsNone(foo.expires)
        self.assertIsNone(spam.expires)

        cookie = c._cookies['www.acme.com']['/']['fortytwo']
        self.assertIsNotNone(cookie.value)
        self.assertEqual(cookie.value, '')

        # there should be a distinction between a present but empty value
        # (above) and a value that's entirely missing (below)

        cookie = c._cookies['www.acme.com']['/']['holyhandgrenade']
        self.assertIsNone(cookie.value)

    def test_ns_parser_special_names(self):
        # names such as 'expires' are not special in first name=value pair
        # of Set-Cookie: header
        # c = CookieJar()
        c = SqliteCookieJar(database_path=hardcoded_database_path)
        c.connect()
        interact_netscape(c, "http://www.acme.com/", 'expires=eggs')
        interact_netscape(c, "http://www.acme.com/", 'version=eggs; spam=eggs')

        cookies = c._cookies["www.acme.com"]["/"]
        self.assertIn('expires', cookies)
        self.assertIn('version', cookies)
        c.close()

    def test_expires(self):
        # if expires is in future, keep cookie...
        # c = CookieJar()
        c = SqliteCookieJar(database_path=hardcoded_database_path)
        c.connect()
        future = time2netscape(time.time()+3600)

        with warnings_helper.check_no_warnings(self):
            headers = [f"Set-Cookie: FOO=BAR; path=/; expires={future}"]
            req = urllib.request.Request("http://www.coyote.com/")
            res = FakeResponse(headers, "http://www.coyote.com/")
            cookies = c.make_cookies(res, req)
            self.assertEqual(len(cookies), 1)
            self.assertEqual(time2netscape(cookies[0].expires), future)

        interact_netscape(c, "http://www.acme.com/", 'spam="bar"; expires=%s' %
                          future)
        self.assertEqual(len(c), 1)
        now = time2netscape(time.time()-1)
        # ... and if in past or present, discard it
        interact_netscape(c, "http://www.acme.com/", 'foo="eggs"; expires=%s' %
                          now)
        h = interact_netscape(c, "http://www.acme.com/")
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)
        self.assertNotIn("foo", h)

        # max-age takes precedence over expires, and zero max-age is request to
        # delete both new cookie and any old matching cookie
        interact_netscape(c, "http://www.acme.com/", 'eggs="bar"; expires=%s' %
                          future)
        interact_netscape(c, "http://www.acme.com/", 'bar="bar"; expires=%s' %
                          future)
        self.assertEqual(len(c), 3)
        interact_netscape(c, "http://www.acme.com/", 'eggs="bar"; '
                          'expires=%s; max-age=0' % future)
        interact_netscape(c, "http://www.acme.com/", 'bar="bar"; '
                          'max-age=0; expires=%s' % future)
        h = interact_netscape(c, "http://www.acme.com/")
        self.assertEqual(len(c), 1)

        # test expiry at end of session for cookies with no expires attribute
        interact_netscape(c, "http://www.rhubarb.net/", 'whum="fizz"')
        self.assertEqual(len(c), 2)
        c.clear_session_cookies()
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)

        # test if fractional expiry is accepted
        cookie  = Cookie(0, "name", "value",
                         None, False, "www.python.org",
                         True, False, "/",
                         False, False, "1444312383.018307",
                         False, None, None,
                         {})
        self.assertEqual(cookie.expires, 1444312383)
        c.close()

        # XXX RFC 2965 expiry rules (some apply to V0 too)

    def test_default_path(self):
        # RFC 2965
        pol = DefaultCookiePolicy(rfc2965=True)



        def _assert_cookie_path_is_present(
            cookiejar,
            path,
            domain):

            tmp_request = urllib.request.Request(
                f"http://www.acme.com{path}",
                data=None,
                headers={},
                origin_req_host=None,
                unverifiable=False,
                method="GET")

            cookie_list = cookiejar._cookies_for_domain(
                domain=domain, request=tmp_request)

            self.assertEqual(len(cookie_list), 1)
            tmp_cookie = cookie_list[0]
            self.assertEqual(tmp_cookie.path, path)


        #c = CookieJar(pol)
        with SqliteCookieJar(":memory:", pol) as c:
            interact_2965(c, "http://www.acme.com/", 'spam="bar"; Version="1"')
            #self.assertIn("/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/", domain="www.acme.com")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:", pol) as c:
            interact_2965(c, "http://www.acme.com/blah", 'eggs="bar"; Version="1"')
            # self.assertIn("/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/", domain="www.acme.com")


        #c = CookieJar(pol)
        with SqliteCookieJar(":memory:", pol) as c:
            interact_2965(c, "http://www.acme.com/blah/rhubarb",
                          'eggs="bar"; Version="1"')
            # self.assertIn("/blah/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/blah/", domain="www.acme.com")


        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:", pol) as c:
            interact_2965(c, "http://www.acme.com/blah/rhubarb/",
                          'eggs="bar"; Version="1"')
            # self.assertIn("/blah/rhubarb/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/blah/rhubarb/", domain="www.acme.com")


        # Netscape

        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://www.acme.com/", 'spam="bar"')
            # self.assertIn("/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/", domain="www.acme.com",)


        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://www.acme.com/blah", 'eggs="bar"')
            # self.assertIn("/", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/", domain="www.acme.com")


        # c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://www.acme.com/blah/rhubarb", 'eggs="bar"')
            # self.assertIn("/blah", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/blah", domain="www.acme.com")


        # c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://www.acme.com/blah/rhubarb/", 'eggs="bar"')
            # self.assertIn("/blah/rhubarb", c._cookies["www.acme.com"])
            _assert_cookie_path_is_present(c, path="/blah/rhubarb", domain="www.acme.com")


    def test_default_path_with_query(self):
        #cj = CookieJar()
        with SqliteCookieJar(":memory:") as cj:
            uri = "http://example.com/?spam/eggs"
            value = 'eggs="bar"'
            interact_netscape(cj, uri, value)
            # Default path does not include query, so is "/", not "/?spam".
            self.assertIn("/", cj._cookies["example.com"])
            # Cookie is sent back to the same URI.
            self.assertEqual(interact_netscape(cj, uri), value)


    def test_request_path(self):
        # with parameters
        req = urllib.request.Request(
            "http://www.example.com/rheum/rhaponticum;"
            "foo=bar;sing=song?apples=pears&spam=eggs#ni")
        self.assertEqual(request_path(req),
                         "/rheum/rhaponticum;foo=bar;sing=song")
        # without parameters
        req = urllib.request.Request(
            "http://www.example.com/rheum/rhaponticum?"
            "apples=pears&spam=eggs#ni")
        self.assertEqual(request_path(req), "/rheum/rhaponticum")
        # missing final slash
        req = urllib.request.Request("http://www.example.com")
        self.assertEqual(request_path(req), "/")

    def test_path_prefix_match(self):
        pol = DefaultCookiePolicy()
        strict_ns_path_pol = DefaultCookiePolicy(strict_ns_set_path=True)

        #c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            base_url = "http://bar.com"
            interact_netscape(c, base_url, 'spam=eggs; Path=/foo')
            cookie = c._cookies['bar.com']['/foo']['spam']

            for path, ok in [('/foo', True),
                             ('/foo/', True),
                             ('/foo/bar', True),
                             ('/', False),
                             ('/foobad/foo', False)]:
                url = f'{base_url}{path}'
                req = urllib.request.Request(url)
                h = interact_netscape(c, url)
                if ok:
                    self.assertIn('spam=eggs', h, f"cookie not set for {path}")
                    self.assertTrue(strict_ns_path_pol.set_ok_path(cookie, req))
                else:
                    self.assertNotIn('spam=eggs', h, f"cookie set for {path}")
                    self.assertFalse(strict_ns_path_pol.set_ok_path(cookie, req))

    def test_request_port(self):
        req = urllib.request.Request("http://www.acme.com:1234/",
                                     headers={"Host": "www.acme.com:4321"})
        self.assertEqual(request_port(req), "1234")
        req = urllib.request.Request("http://www.acme.com/",
                                     headers={"Host": "www.acme.com:4321"})
        self.assertEqual(request_port(req), DEFAULT_HTTP_PORT)

    def test_request_host(self):
        # this request is illegal (RFC2616, 14.2.3)
        req = urllib.request.Request("http://1.1.1.1/",
                                     headers={"Host": "www.acme.com:80"})
        # libwww-perl wants this response, but that seems wrong (RFC 2616,
        # section 5.2, point 1., and RFC 2965 section 1, paragraph 3)
        #self.assertEqual(request_host(req), "www.acme.com")
        self.assertEqual(request_host(req), "1.1.1.1")
        req = urllib.request.Request("http://www.acme.com/",
                                     headers={"Host": "irrelevant.com"})
        self.assertEqual(request_host(req), "www.acme.com")
        # port shouldn't be in request-host
        req = urllib.request.Request("http://www.acme.com:2345/resource.html",
                                     headers={"Host": "www.acme.com:5432"})
        self.assertEqual(request_host(req), "www.acme.com")

    def test_is_HDN(self):
        self.assertTrue(is_HDN("foo.bar.com"))
        self.assertTrue(is_HDN("1foo2.3bar4.5com"))
        self.assertFalse(is_HDN("192.168.1.1"))
        self.assertFalse(is_HDN(""))
        self.assertFalse(is_HDN("."))
        self.assertFalse(is_HDN(".foo.bar.com"))
        self.assertFalse(is_HDN("..foo"))
        self.assertFalse(is_HDN("foo."))

    def test_reach(self):
        self.assertEqual(reach("www.acme.com"), ".acme.com")
        self.assertEqual(reach("acme.com"), "acme.com")
        self.assertEqual(reach("acme.local"), ".local")
        self.assertEqual(reach(".local"), ".local")
        self.assertEqual(reach(".com"), ".com")
        self.assertEqual(reach("."), ".")
        self.assertEqual(reach(""), "")
        self.assertEqual(reach("192.168.0.1"), "192.168.0.1")

    def test_domain_match(self):
        self.assertTrue(domain_match("192.168.1.1", "192.168.1.1"))
        self.assertFalse(domain_match("192.168.1.1", ".168.1.1"))
        self.assertTrue(domain_match("x.y.com", "x.Y.com"))
        self.assertTrue(domain_match("x.y.com", ".Y.com"))
        self.assertFalse(domain_match("x.y.com", "Y.com"))
        self.assertTrue(domain_match("a.b.c.com", ".c.com"))
        self.assertFalse(domain_match(".c.com", "a.b.c.com"))
        self.assertTrue(domain_match("example.local", ".local"))
        self.assertFalse(domain_match("blah.blah", ""))
        self.assertFalse(domain_match("", ".rhubarb.rhubarb"))
        self.assertTrue(domain_match("", ""))

        self.assertTrue(user_domain_match("acme.com", "acme.com"))
        self.assertFalse(user_domain_match("acme.com", ".acme.com"))
        self.assertTrue(user_domain_match("rhubarb.acme.com", ".acme.com"))
        self.assertTrue(user_domain_match("www.rhubarb.acme.com", ".acme.com"))
        self.assertTrue(user_domain_match("x.y.com", "x.Y.com"))
        self.assertTrue(user_domain_match("x.y.com", ".Y.com"))
        self.assertFalse(user_domain_match("x.y.com", "Y.com"))
        self.assertTrue(user_domain_match("y.com", "Y.com"))
        self.assertFalse(user_domain_match(".y.com", "Y.com"))
        self.assertTrue(user_domain_match(".y.com", ".Y.com"))
        self.assertTrue(user_domain_match("x.y.com", ".com"))
        self.assertFalse(user_domain_match("x.y.com", "com"))
        self.assertFalse(user_domain_match("x.y.com", "m"))
        self.assertFalse(user_domain_match("x.y.com", ".m"))
        self.assertFalse(user_domain_match("x.y.com", ""))
        self.assertFalse(user_domain_match("x.y.com", "."))
        self.assertTrue(user_domain_match("192.168.1.1", "192.168.1.1"))
        # not both HDNs, so must string-compare equal to match
        self.assertFalse(user_domain_match("192.168.1.1", ".168.1.1"))
        self.assertFalse(user_domain_match("192.168.1.1", "."))
        # empty string is a special case
        self.assertFalse(user_domain_match("192.168.1.1", ""))

    def test_wrong_domain(self):
        # Cookies whose effective request-host name does not domain-match the
        # domain are rejected.

        # XXX far from complete
        # c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_2965(c, "http://www.nasty.com/",
                          'foo=bar; domain=friendly.org; Version="1"')
            self.assertEqual(len(c), 0)

    def test_strict_domain(self):
        # Cookies whose domain is a country-code tld like .co.uk should
        # not be set if CookiePolicy.strict_domain is true.
        cp = DefaultCookiePolicy(strict_domain=True)
        #cj = CookieJar(policy=cp)
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(cj, "http://example.co.uk/", 'no=problemo')
            interact_netscape(cj, "http://example.co.uk/",
                              'okey=dokey; Domain=.example.co.uk')
            self.assertEqual(len(cj), 2)
            for pseudo_tld in [".co.uk", ".org.za", ".tx.us", ".name.us"]:
                interact_netscape(cj, "http://example.%s/" % pseudo_tld,
                                  'spam=eggs; Domain=.co.uk')
                self.assertEqual(len(cj), 2)

    def test_two_component_domain_ns(self):
        # Netscape: .www.bar.com, www.bar.com, .bar.com, bar.com, no domain
        # should all get accepted, as should .acme.com, acme.com and no domain
        # for 2-component domains like acme.com.
        # c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            # two-component V0 domain is OK
            interact_netscape(c, "http://foo.net/", 'ns=bar')
            self.assertEqual(len(c), 1)
            self.assertEqual(c._cookies["foo.net"]["/"]["ns"].value, "bar")
            self.assertEqual(interact_netscape(c, "http://foo.net/"), "ns=bar")
            # *will* be returned to any other domain (unlike RFC 2965)...
            self.assertEqual(interact_netscape(c, "http://www.foo.net/"),
                             "ns=bar")
            # ...unless requested otherwise
            pol = DefaultCookiePolicy(
                strict_ns_domain=DefaultCookiePolicy.DomainStrictNonDomain)
            c.set_policy(pol)
            self.assertEqual(interact_netscape(c, "http://www.foo.net/"), "")

            # unlike RFC 2965, even explicit two-component domain is OK,
            # because .foo.net matches foo.net
            interact_netscape(c, "http://foo.net/foo/",
                              'spam1=eggs; domain=foo.net')
            # even if starts with a dot -- in NS rules, .foo.net matches foo.net!
            interact_netscape(c, "http://foo.net/foo/bar/",
                              'spam2=eggs; domain=.foo.net')
            self.assertEqual(len(c), 3)
            self.assertEqual(c._cookies[".foo.net"]["/foo"]["spam1"].value,
                             "eggs")
            self.assertEqual(c._cookies[".foo.net"]["/foo/bar"]["spam2"].value,
                             "eggs")
            self.assertEqual(interact_netscape(c, "http://foo.net/foo/bar/"),
                             "spam2=eggs; spam1=eggs; ns=bar")

            # top-level domain is too general
            interact_netscape(c, "http://foo.net/", 'nini="ni"; domain=.net')
            self.assertEqual(len(c), 3)

    ##         # Netscape protocol doesn't allow non-special top level domains (such
    ##         # as co.uk) in the domain attribute unless there are at least three
    ##         # dots in it.
            # Oh yes it does!  Real implementations don't check this, and real
            # cookies (of course) rely on that behaviour.
            interact_netscape(c, "http://foo.co.uk", 'nasty=trick; domain=.co.uk')
    ##         self.assertEqual(len(c), 2)
            self.assertEqual(len(c), 4)

    def test_localhost_domain(self):
        # c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://localhost", "foo=bar; domain=localhost;")

            self.assertEqual(len(c), 1)

    def test_localhost_domain_contents(self):
        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://localhost", "foo=bar; domain=localhost;")

            self.assertEqual(c._cookies[".localhost"]["/"]["foo"].value, "bar")

    def test_localhost_domain_contents_2(self):
        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://localhost", "foo=bar;")

            self.assertEqual(c._cookies["localhost.local"]["/"]["foo"].value, "bar")

    def test_evil_nonlocal_domain(self):
        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://evil.com", "foo=bar; domain=.localhost")

            self.assertEqual(len(c), 0)

    def test_evil_local_domain(self):
        # c = CookieJar()

            interact_netscape(c, "http://localhost", "foo=bar; domain=.evil.com")

            self.assertEqual(len(c), 0)

    def test_evil_local_domain_2(self):
        #c = CookieJar()
        with SqliteCookieJar(":memory:") as c:
            interact_netscape(c, "http://localhost", "foo=bar; domain=.someother.local")

            self.assertEqual(len(c), 0)

    def test_two_component_domain_rfc2965(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        #c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            # two-component V1 domain is OK
            interact_2965(c, "http://foo.net/", 'foo=bar; Version="1"')
            self.assertEqual(len(c), 1)
            self.assertEqual(c._cookies["foo.net"]["/"]["foo"].value, "bar")
            self.assertEqual(interact_2965(c, "http://foo.net/"),
                             "$Version=1; foo=bar")
            # won't be returned to any other domain (because domain was implied)
            self.assertEqual(interact_2965(c, "http://www.foo.net/"), "")

            # unless domain is given explicitly, because then it must be
            # rewritten to start with a dot: foo.net --> .foo.net, which does
            # not domain-match foo.net
            interact_2965(c, "http://foo.net/foo",
                          'spam=eggs; domain=foo.net; path=/foo; Version="1"')
            self.assertEqual(len(c), 1)
            self.assertEqual(interact_2965(c, "http://foo.net/foo"),
                             "$Version=1; foo=bar")

            # explicit foo.net from three-component domain www.foo.net *does* get
            # set, because .foo.net domain-matches .foo.net
            interact_2965(c, "http://www.foo.net/foo/",
                          'spam=eggs; domain=foo.net; Version="1"')
            self.assertEqual(c._cookies[".foo.net"]["/foo/"]["spam"].value,
                             "eggs")
            self.assertEqual(len(c), 2)
            self.assertEqual(interact_2965(c, "http://foo.net/foo/"),
                             "$Version=1; foo=bar")
            self.assertEqual(interact_2965(c, "http://www.foo.net/foo/"),
                             '$Version=1; spam=eggs; $Domain="foo.net"')

            # top-level domain is too general
            interact_2965(c, "http://foo.net/",
                          'ni="ni"; domain=".net"; Version="1"')
            self.assertEqual(len(c), 2)

            # RFC 2965 doesn't require blocking this
            interact_2965(c, "http://foo.co.uk/",
                          'nasty=trick; domain=.co.uk; Version="1"')
            self.assertEqual(len(c), 3)

    def test_domain_allow(self):
        # c = CookieJar(policy=DefaultCookiePolicy(
        #     blocked_domains=["acme.com"],
        #     allowed_domains=["www.acme.com"]))
        with SqliteCookieJar(":memory:", policy=DefaultCookiePolicy(
            blocked_domains=["acme.com"],
            allowed_domains=["www.acme.com"])) as c:

            req = urllib.request.Request("http://acme.com/")
            headers = ["Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/"]
            res = FakeResponse(headers, "http://acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 0)

            req = urllib.request.Request("http://www.acme.com/")
            res = FakeResponse(headers, "http://www.acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            req = urllib.request.Request("http://www.coyote.com/")
            res = FakeResponse(headers, "http://www.coyote.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            # set a cookie with non-allowed domain...
            req = urllib.request.Request("http://www.coyote.com/")
            res = FakeResponse(headers, "http://www.coyote.com/")
            cookies = c.make_cookies(res, req)
            c.set_cookie(cookies[0])
            self.assertEqual(len(c), 2)
            # ... and check is doesn't get returned
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

    def test_domain_block(self):
        pol = DefaultCookiePolicy(
            rfc2965=True, blocked_domains=[".acme.com"])
        #c = CookieJar(policy=pol)
        with SqliteCookieJar(":memory:") as c:
            headers = ["Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/"]

            req = urllib.request.Request("http://www.acme.com/")
            res = FakeResponse(headers, "http://www.acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 0)

            p = pol.set_blocked_domains(["acme.com"])
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            c.clear()
            req = urllib.request.Request("http://www.roadrunner.net/")
            res = FakeResponse(headers, "http://www.roadrunner.net/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)
            req = urllib.request.Request("http://www.roadrunner.net/")
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))
            self.assertTrue(req.has_header("Cookie2"))

            c.clear()
            pol.set_blocked_domains([".acme.com"])
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            # set a cookie with blocked domain...
            req = urllib.request.Request("http://www.acme.com/")
            res = FakeResponse(headers, "http://www.acme.com/")
            cookies = c.make_cookies(res, req)
            c.set_cookie(cookies[0])
            self.assertEqual(len(c), 2)
            # ... and check is doesn't get returned
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

            c.clear()

            pol.set_blocked_domains([])
            req = urllib.request.Request("http://acme.com/")
            res = FakeResponse(headers, "http://acme.com/")
            cookies = c.make_cookies(res, req)
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            req = urllib.request.Request("http://acme.com/")
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))

            req = urllib.request.Request("http://badacme.com/")
            c.add_cookie_header(req)
            self.assertFalse(pol.return_ok(cookies[0], req))
            self.assertFalse(req.has_header("Cookie"))

            p = pol.set_blocked_domains(["acme.com"])
            req = urllib.request.Request("http://acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

            req = urllib.request.Request("http://badacme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

    def test_secure(self):
        for ns in True, False:
            for whitespace in " ", "":
                # c = CookieJar()
                with SqliteCookieJar(":memory:") as c:
                    if ns:
                        pol = DefaultCookiePolicy(rfc2965=False)
                        int = interact_netscape
                        vs = ""
                    else:
                        pol = DefaultCookiePolicy(rfc2965=True)
                        int = interact_2965
                        vs = "; Version=1"
                    c.set_policy(pol)
                    url = "http://www.acme.com/"
                    int(c, url, "foo1=bar%s%s" % (vs, whitespace))
                    int(c, url, "foo2=bar%s; secure%s" %  (vs, whitespace))
                    self.assertFalse(
                        c._cookies["www.acme.com"]["/"]["foo1"].secure,
                        "non-secure cookie registered secure")
                    self.assertTrue(
                        c._cookies["www.acme.com"]["/"]["foo2"].secure,
                        "secure cookie registered non-secure")

    def test_secure_block(self):
        pol = DefaultCookiePolicy()
        # c = CookieJar(policy=pol)
        with SqliteCookieJar(":memory:") as c:

            headers = ["Set-Cookie: session=narf; secure; path=/"]
            req = urllib.request.Request("https://www.acme.com/")
            res = FakeResponse(headers, "https://www.acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            req = urllib.request.Request("https://www.acme.com/")
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))

            req = urllib.request.Request("http://www.acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

            # secure websocket protocol
            req = urllib.request.Request("wss://www.acme.com/")
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))

            # non-secure websocket protocol
            req = urllib.request.Request("ws://www.acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

    def test_custom_secure_protocols(self):
        pol = DefaultCookiePolicy(secure_protocols=["foos"])
        #c = CookieJar(policy=pol)
        with SqliteCookieJar(":memory:", policy=pol) as c:
            headers = ["Set-Cookie: session=narf; secure; path=/"]
            req = urllib.request.Request("https://www.acme.com/")
            res = FakeResponse(headers, "https://www.acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            # test https removed from secure protocol list
            req = urllib.request.Request("https://www.acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

            req = urllib.request.Request("http://www.acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

            req = urllib.request.Request("foos://www.acme.com/")
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))

            req = urllib.request.Request("foo://www.acme.com/")
            c.add_cookie_header(req)
            self.assertFalse(req.has_header("Cookie"))

    def test_quote_cookie_value(self):
        #c = CookieJar(policy=DefaultCookiePolicy(rfc2965=True))
        with SqliteCookieJar(":memory:", policy=DefaultCookiePolicy(rfc2965=True)) as c:
            interact_2965(c, "http://www.acme.com/", r'foo=\b"a"r; Version=1')
            h = interact_2965(c, "http://www.acme.com/")
            self.assertEqual(h, r'$Version=1; foo=\\b\"a\"r')

    def test_missing_final_slash(self):
        # Missing slash from request URL's abs_path should be assumed present.
        url = "http://www.acme.com"
        # c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        with SqliteCookieJar(":memory:", policy=DefaultCookiePolicy(rfc2965=True)) as c:
            interact_2965(c, url, "foo=bar; Version=1")
            req = urllib.request.Request(url)
            self.assertEqual(len(c), 1)
            c.add_cookie_header(req)
            self.assertTrue(req.has_header("Cookie"))

    def test_domain_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, "spam=eggs; Version=1")
            h = interact_2965(c, url)
            self.assertNotIn("Domain", h,
                         "absent domain returned with domain present")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, 'spam=eggs; Version=1; Domain=.bar.com')
            h = interact_2965(c, url)
            self.assertIn('$Domain=".bar.com"', h, "domain not returned")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            # note missing initial dot in Domain
            interact_2965(c, url, 'spam=eggs; Version=1; Domain=bar.com')
            h = interact_2965(c, url)
            self.assertIn('$Domain="bar.com"', h, "domain not returned")

    def test_path_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, "spam=eggs; Version=1")
            h = interact_2965(c, url)
            self.assertNotIn("Path", h, "absent path returned with path present")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, 'spam=eggs; Version=1; Path=/')
            h = interact_2965(c, url)
            self.assertIn('$Path="/"', h, "path not returned")

    def test_port_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)

        #c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, "spam=eggs; Version=1")
            h = interact_2965(c, url)
            self.assertNotIn("Port", h, "absent port returned with port present")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, "spam=eggs; Version=1; Port")
            h = interact_2965(c, url)
            self.assertRegex(h, r"\$Port([^=]|$)",
                             "port with no value not returned with no value")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, 'spam=eggs; Version=1; Port="80"')
            h = interact_2965(c, url)
            self.assertIn('$Port="80"', h,
                          "port with single value not returned with single value")

        # c = CookieJar(pol)
        with SqliteCookieJar(":memory:") as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, 'spam=eggs; Version=1; Port="80,8080"')
            h = interact_2965(c, url)
            self.assertIn('$Port="80,8080"', h,
                          "port with multiple values not returned with multiple "
                          "values")

    def test_no_return_comment(self):
        # c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        with SqliteCookieJar(":memory:", DefaultCookiePolicy(rfc2965=True)) as c:
            url = "http://foo.bar.com/"
            interact_2965(c, url, 'spam=eggs; Version=1; '
                          'Comment="does anybody read these?"; '
                          'CommentURL="http://foo.bar.net/comment.html"')
            h = interact_2965(c, url)
            self.assertNotIn("Comment", h,
                "Comment or CommentURL cookie-attributes returned to server")

    def test_Cookie_iterator(self):
        # cs = CookieJar(DefaultCookiePolicy(rfc2965=True))
        with SqliteCookieJar(":memory:", DefaultCookiePolicy(rfc2965=True)) as cs:
            # add some random cookies
            interact_2965(cs, "http://blah.spam.org/", 'foo=eggs; Version=1; '
                          'Comment="does anybody read these?"; '
                          'CommentURL="http://foo.bar.net/comment.html"')
            interact_netscape(cs, "http://www.acme.com/blah/", "spam=bar; secure")
            interact_2965(cs, "http://www.acme.com/blah/",
                          "foo=bar; secure; Version=1")
            interact_2965(cs, "http://www.acme.com/blah/",
                          "foo=bar; path=/; Version=1")
            interact_2965(cs, "http://www.sol.no",
                          r'bang=wallop; version=1; domain=".sol.no"; '
                          r'port="90,100, 80,8080"; '
                          r'max-age=100; Comment = "Just kidding! (\"|\\\\) "')

            versions = [1, 0, 1, 1, 1]
            names = ["foo", "spam", "foo", "foo", "bang"]
            domains = ["blah.spam.org", "www.acme.com", "www.acme.com",
                       "www.acme.com", ".sol.no"]
            paths = ["/", "/blah", "/blah/", "/", "/"]

            for i in range(4):
                i = 0
                for c in cs:
                    self.assertIsInstance(c, Cookie)
                    self.assertEqual(c.version, versions[i])
                    self.assertEqual(c.name, names[i])
                    self.assertEqual(c.domain, domains[i])
                    self.assertEqual(c.path, paths[i])
                    i = i + 1

    def test_parse_ns_headers(self):
        # missing domain value (invalid cookie)
        self.assertEqual(
            parse_ns_headers(["foo=bar; path=/; domain"]),
            [[("foo", "bar"),
              ("path", "/"), ("domain", None), ("version", "0")]]
            )
        # invalid expires value
        self.assertEqual(
            parse_ns_headers(["foo=bar; expires=Foo Bar 12 33:22:11 2000"]),
            [[("foo", "bar"), ("expires", None), ("version", "0")]]
            )
        # missing cookie value (valid cookie)
        self.assertEqual(
            parse_ns_headers(["foo"]),
            [[("foo", None), ("version", "0")]]
            )
        # missing cookie values for parsed attributes
        self.assertEqual(
            parse_ns_headers(['foo=bar; expires']),
            [[('foo', 'bar'), ('expires', None), ('version', '0')]])
        self.assertEqual(
            parse_ns_headers(['foo=bar; version']),
            [[('foo', 'bar'), ('version', None)]])
        # shouldn't add version if header is empty
        self.assertEqual(parse_ns_headers([""]), [])

    def test_bad_cookie_header(self):

        def cookiejar_from_cookie_headers(headers):
            # c = CookieJar()
            c = SqliteCookieJar(":memory:")
            c.connect()
            req = urllib.request.Request("http://www.example.com/")
            r = FakeResponse(headers, "http://www.example.com/")
            c.extract_cookies(r, req)
            return c

        future = time2netscape(time.time()+3600)

        # none of these bad headers should cause an exception to be raised
        for headers in [
            ["Set-Cookie: "],  # actually, nothing wrong with this
            ["Set-Cookie2: "],  # ditto
            # missing domain value
            ["Set-Cookie2: a=foo; path=/; Version=1; domain"],
            # bad max-age
            ["Set-Cookie: b=foo; max-age=oops"],
            # bad version
            ["Set-Cookie: b=foo; version=spam"],
            ["Set-Cookie:; Expires=%s" % future],
            ]:
            c = cookiejar_from_cookie_headers(headers)
            # these bad cookies shouldn't be set
            self.assertEqual(len(c), 0)
            c.close()

        # cookie with invalid expires is treated as session cookie
        headers = ["Set-Cookie: c=foo; expires=Foo Bar 12 33:22:11 2000"]
        c = cookiejar_from_cookie_headers(headers)
        # cookie = c._cookies["www.example.com"]["/"]["c"]
        tmp_request = urllib.request.Request(
            "http://www.example.com",
            data=None,
            headers={},
            origin_req_host=None,
            unverifiable=False,
            method="GET")
        cookie_list = c._cookies_for_domain(domain="www.example.com", request=tmp_request)
        self.assertEqual(len(cookie_list), 1)
        cookie = cookie_list[0]
        self.assertEqual(cookie.name, "c")
        self.assertIsNone(cookie.expires)
        self.assertEqual(cookie.path, "/")