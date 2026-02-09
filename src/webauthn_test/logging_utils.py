"""Logging handlers and configuration helpers.

This module provides a combined size- and time-based rotating file handler and
applies a deterministic logger configuration for the Flask application.

Constraints:
- logs are written to local filesystem targets configured by environment
- rotation triggers on either midnight rollover or max size threshold
"""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any


class SizeAndTimeRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename: str,
        max_kb: int,
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 14,
        encoding: str | None = "utf-8",
    ) -> None:
        super().__init__(
            filename=filename,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=encoding,
        )
        self.max_bytes = max_kb * 1024

    def shouldRollover(self, record: logging.LogRecord) -> int:  # noqa: N802
        if super().shouldRollover(record):
            return 1

        if self.max_bytes <= 0:
            return 0

        if self.stream is None:
            self.stream = self._open()
        msg = f"{self.format(record)}\n"
        self.stream.seek(0, 2)
        if self.stream.tell() + len(msg.encode("utf-8")) >= self.max_bytes:
            return 1
        return 0


def configure_logging(
    app_name: str,
    log_dir: str,
    log_filename: str,
    log_level: str,
    log_max_kb: int,
) -> None:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    handler = SizeAndTimeRotatingFileHandler(
        filename=str(log_path / log_filename),
        max_kb=log_max_kb,
    )
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger = logging.getLogger(app_name)
    logger.setLevel(log_level.upper())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False


def flask_log_config(app_logger: logging.Logger) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"default": {"class": "logging.NullHandler"}},
        "loggers": {app_logger.name: {"handlers": ["default"]}},
    }
