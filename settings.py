from pathlib import Path
from dotenv import load_dotenv
import os

DEV = True

if DEV:
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

CLIENT_ID = os.environ.get("CLIENT_ID", "")

CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

TOKEN_URL = os.environ.get("TOKEN_URL", "http://woodwork4.ddns.net:3005/oauth2/token")

URL = os.environ.get("URL", "http://127.0.0.1:8000/api/v1")

PROJECTS_DIR = os.environ.get("PROJECTS_DIR", "")


LOGGER = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - level: %(levelname)s - loc: %(name)s - func: %(funcName)s - msg: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/watchdog.log",
            "level": "DEBUG",
            "maxBytes": 1048574,
            "backupCount": 3,
            "formatter": "simple"
        }
    },
    "loggers": {
        "client": {
            "level": "DEBUG",
            "handlers": [
                "console",
                "file"
            ],
            "propagate": True
        },
        "__main__": {
            "level": "DEBUG",
            "handlers": [
                "console",
                "file"
            ],
            "propagate": True
        }
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console", "file"
        ],
    }
}
