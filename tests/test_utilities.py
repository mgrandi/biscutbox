from http.cookiejar import Cookie
import urllib.request


def assert_cookie_equality(cookie_one:Cookie, cookie_two:Cookie):
    '''
    http.cookiejar.Cookie doesn't implement __eq__ so we can't do
    `assert cookie_one == cookie_two`, grumble
    this is a helper that manually checks for equality between
    two cookie objects

    :param cookie_one: the first cookie to check against cookie_two
    :param cookie_two: the second cookie to check against cookie_one
    '''

    assert cookie_one.version == cookie_two.version
    assert cookie_one.name == cookie_two.name
    assert cookie_one.value == cookie_two.value
    assert cookie_one.port == cookie_two.port
    assert cookie_one.port_specified == cookie_two.port_specified
    assert cookie_one.domain == cookie_two.domain
    assert cookie_one.domain_specified == cookie_two.domain_specified
    assert cookie_one.domain_initial_dot == cookie_two.domain_initial_dot
    assert cookie_one.path == cookie_two.path
    assert cookie_one.path_specified == cookie_two.path_specified
    assert cookie_one.secure == cookie_two.secure
    assert cookie_one.expires == cookie_two.expires
    assert cookie_one.discard == cookie_two.discard
    assert cookie_one.comment == cookie_two.comment
    assert cookie_one.comment_url == cookie_two.comment_url
    assert cookie_one._rest == cookie_two._rest
    assert cookie_one.rfc2109 == cookie_two.rfc2109



def create_simple_cookie(name:str, value:str, domain:str) -> Cookie:
    '''helper to create a single cookie with a name and a value

    :param name: the cookie name
    :param value: the cookie value
    :param domain: the cookie domain
    :return: the Cookie with the name and value set
    '''
    test_cookie = Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
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

    return test_cookie


def create_dummy_request(url:str, method:str) -> urllib.request.Request:
    '''
    create a dummy urllib.request.Request object
    :param url: the URL
    :param method: the HTTP method
    :return: a urllib.request.Request object
    '''

    dummy_request = urllib.request.Request(
        url,
        data=None,
        headers={},
        origin_req_host=None,
        unverifiable=False,
        method="GET")

    return dummy_request