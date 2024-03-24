import mimetypes
import socket
import logging

import constants.config as config
from multiprocessing import Process
from urllib.parse import urlparse, unquote_plus
from http.server import HTTPServer, BaseHTTPRequestHandler

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from datetime import datetime


class RequestsHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa
        router = urlparse(self.path).path
        match router:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                if router.startswith("/assets"):
                    file = config.BASE_DIR.joinpath(router[1:])
                else:
                    file = config.BASE_DIR.joinpath("assets", router[1:])

                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def do_POST(self):  # noqa
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size)).decode()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data.encode(), (config.SOCKET_HOST, config.SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mimetype = (
            mimetypes.guess_type(filename)[0]
            if mimetypes.guess_type(filename)[0]
            else "text/plain"
        )
        self.send_header("Content-type", mimetype)
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


def save_data(data):
    client = MongoClient(config.MONGODB_URI, server_api=ServerApi("1"))
    db = client[config.MONGODB_DB]
    parse_data = unquote_plus(data.decode())
    try:
        parse_data = {
            key: value for key, value in [el.split("=") for el in parse_data.split("&")]
        }
        parse_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        db[config.MONGODB_COLLECTION].insert_one(parse_data)
    except ValueError as e:
        logging.error(f"Parse error: {e}")
    except Exception as e:
        logging.error(f"Failed to save: {e}")
    finally:
        client.close()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def run_http_server():
    setup_logging()
    httpd = HTTPServer((config.HTTP_HOST, config.HTTP_PORT), RequestsHandler)  # noqa
    logging.info(f"HTTP Server started on http://{config.HTTP_HOST}:{config.HTTP_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"HTTP Server error: {e}")
    finally:
        httpd.server_close()
        logging.info("HTTP Server stopped")


def run_socket_server():
    setup_logging()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.SOCKET_HOST, config.SOCKET_PORT))
    logging.info(
        f"Socket Server started on udp://{config.SOCKET_HOST}:{config.SOCKET_PORT}"
    )
    try:
        while True:
            data, addr = sock.recvfrom(config.BUFFER_SIZE)
            logging.info(f"Received message from {addr}: {data.decode()}")
            save_data(data)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Socket Server error: {e}")
    finally:
        sock.close()
        logging.info("Socket Server stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    http_process = Process(target=run_http_server, name="HTTPServer")
    socket_process = Process(target=run_socket_server, name="SocketServer")

    http_process.start()
    socket_process.start()

    http_process.join()
    socket_process.join()
