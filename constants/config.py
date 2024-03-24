from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

MONGODB_URI = "mongodb://mongodb:27017"
MONGODB_DB = "homework"
MONGODB_COLLECTION = "messages"
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = "0.0.0.0"
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000
