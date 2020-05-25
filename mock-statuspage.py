from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random

class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()
        indicator = random.choice(['none', 'minor', 'major', 'critical'])
        print("Reporting status: {}".format(indicator))
        content = json.dumps({'status': {'indicator': indicator}})
        self.wfile.write(content.encode())

def run(address, port):
    httpd = HTTPServer((address, port), Server)

    print('Starting httpd at {}:{}...'.format(address, port))
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv
    args_dict = dict(enumerate(argv))
    address = args_dict.get(1, '0.0.0.0')
    port    = args_dict.get(2, 8088)

    run(address, port)
