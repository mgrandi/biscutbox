import http.server
import json

import logging
logging.basicConfig(level="DEBUG")

logger = logging.getLogger("DEBUG")

class CookieServingHttpHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        ''' handle get requests'''

        content_length = self.headers.get('content-length')
        length=-1
        if content_length:
            length = int(content_length)
        else:
            length = 0

        post_body = self.rfile.read(length)

        post_body = None
        try:
            post_json = json.loads(post_body)
        except Exception as e:
            logger.error("invalid json in post body")
            self.send_error(400, "invalid json in post body")
            return


        # parse the json config
        cookie_name = post_json["name"]
        cookie_value = post_json["cookie_value"]
        cookie_domain = post_json["domain"]
        cookie_expires = post_json["expires"]
        cookie_httponly = int(post_json["httponly"])
        cookie_maxage = post_json["maxage"]
        cookie_path = post_json["path"]
        cookie_secure = int(post_json["secure"])
        cookie_discard = int(post_json["discard"])
        cookie_comment = post_json["comment"]
        cookie_commentUrl = post_json["commenturl"]
        cookie_samesite = post_json["samesite"]


        set_cookie_line = f"{cookie_name}={cookie_value}; Version=1; Domain={cookie_domain}; " +
        f"Expires={cookie_expires}; Max-Age={cookie_maxage}; Path={cookie_path}; " +
        f"Comment={cookie_comment}; CommentUrl={cookie_commentUrl}; SameSite={cookie_samesite}; "

        if cookie_httponly:
            set_cookie_line += "HttpOnly;"

        if cookie_secure:
            set_cookie_line += "Secure; "

        if cookie_discard:
            set_cookie_line += "Discard; "

        self.send_header("Set-Cookie2", set_cookie_line)


class Main:


    def run(self):
        server_address = ('', 8000)
        httpd = http.server.HTTPServer(server_address, CookieServingHttpHandler)
        httpd.serve_forever()

if __name__ == "__main__":
    m =  Main()
    m.run()