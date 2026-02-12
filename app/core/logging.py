import logging
import sys
from contextvars import ContextVar

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "",
    logging.INFO: GREEN,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: RED,
}

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - [%(request_id)s] - %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_ctx.get() or "-"


class RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.request_id = get_request_id()
        return super().format(record)


class ColoredLevelFormatter(RequestIdFormatter):
    def format(self, record: logging.LogRecord) -> str:
        record.request_id = get_request_id()
        color = LEVEL_COLORS.get(record.levelno, "")
        if color:
            original = record.levelname
            record.levelname = f"{color}{original}{RESET}"
            result = super().format(record)
            record.levelname = original
            return result
        return super().format(record)


def setup_logging(log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    use_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if use_colors:
        formatter = ColoredLevelFormatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    else:
        formatter = RequestIdFormatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
