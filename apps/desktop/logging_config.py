"""Shared diagnostic logging for the desktop and standalone clients."""

from __future__ import annotations

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_PATH = LOG_DIR / "spottransfer.log"
logger = logging.getLogger("spottransfer")

_SECRET_FIELD = re.compile(
    r"(?i)(authorization|cookie|set-cookie)\s*['\"]?\s*[:=]\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\r\n]+)"
)


class _RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return _SECRET_FIELD.sub(r"\1=<redacted>", super().format(record))


def _log_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught application exception",
                    exc_info=(exc_type, exc_value, exc_traceback))


def configure_logging() -> None:
    if logger.handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_PATH, maxBytes=2_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(_RedactingFormatter(
        "%(asctime)s %(levelname)s [%(threadName)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    sys.excepthook = _log_uncaught_exception
