# a file that has some pre set cookie policy objects

from http.cookiejar import CookiePolicy, DefaultCookiePolicy



COOKIE_POLICY_ONLY_EXAMPLE_COM = DefaultCookiePolicy(

    blocked_domains=None,
    allowed_domains=["example.com"])