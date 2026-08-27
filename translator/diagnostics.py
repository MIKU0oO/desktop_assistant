from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import ConfigStore


LOGGER_NAME = "translate_assistant"


def log_path() -> Path:
    return ConfigStore.default_path().with_name("app.log")


def ensure_log_file() -> Path:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def setup_logging() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return

    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        path,
        maxBytes=512 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str = "") -> logging.Logger:
    suffix = f".{name}" if name else ""
    return logging.getLogger(f"{LOGGER_NAME}{suffix}")


def clear_log_file() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.acquire()
            try:
                handler.flush()
                if handler.stream is not None:
                    handler.stream.seek(0)
                    handler.stream.truncate()
            finally:
                handler.release()
            return

    ensure_log_file().write_text("", encoding="utf-8")
