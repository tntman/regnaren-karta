"""The web server for the tests: serves docs/ like `python -m http.server`, but made for
many browsers at once (the tests run side by side, and the offline test fetches ~1 200
files): a long queue for new connections and a thread per request.

    py -3 serve.py <port> <folder>
"""
import sys, functools, http.server, socketserver

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 256          # (http.server's default is 5: connections got refused/stuck)
    allow_reuse_address = True

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass   # (no log line per file)

if __name__ == '__main__':
    port, folder = int(sys.argv[1]), sys.argv[2]
    Server(('', port), functools.partial(Quiet, directory=folder)).serve_forever()
