"""


tornado server serving flask app


"""


import os
import argparse
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from gaseio.app import app

DEFAULT_GASEIO_PORT = 5000
DEFAULT_GASEIO_MAX_CORE = 16
# LOCALHOST = '127.0.0.1'
HOSTNAME = os.environ.get('GASEIO_HOST', 'localhost')
PORT = os.environ.get("GASEIO_PORT", DEFAULT_GASEIO_PORT)
MAX_CORE = int(os.environ.get("GASEIO_MAX_CORE", DEFAULT_GASEIO_MAX_CORE))


def tornado_server(address: str = HOSTNAME, port: int = PORT,
                   max_core: int = MAX_CORE):
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port, address)
    http_server.start(max_core)
    # ioloop = IOLoop.current()
    ioloop = IOLoop.instance()
    # ioloop.add_callback(ioloop.stop)
    ioloop.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, default=HOSTNAME)
    parser.add_argument('-p', '--port', type=int, default=PORT)
    parser.add_argument('-n', '--max-core', type=int, default=MAX_CORE)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    tornado_server(args.address, args.port, args.max_core)
