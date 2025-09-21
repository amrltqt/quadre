import json
import logging
import logging.config

import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE")
LOG_JSON = os.getenv("LOG_JSON", "false").lower() in {"1","true","yes","on"}
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s %(extras)s"
)
LOG_DATEFMT = os.getenv("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S")

_STANDARD_ATTRS = {
    "name","msg","args","levelname","levelno","pathname","filename","module",
    "exc_info","exc_text","stack_info","lineno","funcName","created","msecs",
    "relativeCreated","thread","threadName","processName","process","asctime"
}

IGNORE_KEYS = {k.strip() for k in os.getenv("EXTRA_IGNORE_KEYS","").split(",") if k.strip()}
_STANDARD_ATTRS |= IGNORE_KEYS


class ExtraFormatter(logging.Formatter):
    def format(self, record):
        d = record.__dict__
        extras = {
            k: v for k, v in d.items()
            if k not in _STANDARD_ATTRS and not k.startswith("_") and v is not None
        }
        record.extras = "" if not extras else " " + json.dumps(extras, ensure_ascii=False, default=str)
        return super().format(record)


formatter = ExtraFormatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFMT)

handlers = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "default",
        "level": LOG_LEVEL,
    }
}

if LOG_FILE:
    handlers["file"] = {
        "class": "logging.FileHandler",
        "formatter": "default",
        "level": LOG_LEVEL,
        "filename": LOG_FILE,
    }

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": ExtraFormatter,
            "format": LOG_FORMAT,
            "datefmt": LOG_DATEFMT,
        },
    },
    "handlers": handlers,
    "root": {"level": LOG_LEVEL, "handlers": list(handlers.keys())},
}
logging.config.dictConfig(logging_config)
