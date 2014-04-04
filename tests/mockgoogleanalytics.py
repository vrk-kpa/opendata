import os
import BaseHTTPServer
import threading

here_dir = os.path.dirname(os.path.abspath(__file__))


class MockHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if "feeds/accounts/default" in self.path:
            self.send_response(200)
            self.end_headers()
            fixture = os.path.join(here_dir, "accountsfixture.xml")
            content = open(fixture, "r").read()
        elif "analytics/feeds/data" in self.path:
            if "dataset" in self.path:
                fixture = os.path.join(here_dir, "packagefixture.xml")
            elif "download" in self.path:
                fixture = os.path.join(here_dir, "downloadfixture.xml")
            self.send_response(200)
            self.end_headers()
            content = open(fixture, "r").read()
        else:
            self.send_response(200)
            self.end_headers()
            content = "empty"
        self.wfile.write(content)

    def do_POST(self):
        if "ClientLogin" in self.path:
            self.send_response(200)
            self.end_headers()
            content = "Auth=blah"
        else:
            self.send_response(200)
            self.end_headers()
            content = "empty"
        self.wfile.write(content)

    def do_QUIT(self):
        self.send_response(200)
        self.end_headers()
        self.server.stop = True


class ReusableServer(BaseHTTPServer.HTTPServer):
    allow_reuse_address = 1

    def serve_til_quit(self):
        self.stop = False
        while not self.stop:
            self.handle_request()


def runmockserver():
    server_address = ('localhost', 6969)
    httpd = ReusableServer(server_address,
                           MockHandler)
    httpd_thread = threading.Thread(target=httpd.serve_til_quit)
    httpd_thread.setDaemon(True)
    httpd_thread.start()
    return httpd_thread
