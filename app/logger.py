"""Logging utilities for the application."""

from __future__ import annotations

import logging


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure application logging once for the current process."""

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""

    configure_logging()
    return logging.getLogger(name)
