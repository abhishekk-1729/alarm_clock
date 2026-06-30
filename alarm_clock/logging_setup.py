"""Production style logging configuration.

All user-facing output goes through the CLI/UI layer with clean, colored
text. This module configures a separate rotating log file that captures
structured, technical events for diagnostics. It is never printed to the
terminal directly.
"""

import logging
from logging.handlers import RotatingFileHandler

from alarm_clock.paths import LOG_FILE, ensure_app_dir

_LOGGER_NAME = "alarm_clock"
_CONFIGURED = False


def get_logger() -> logging.Logger:
    """Return the application logger, configuring it on first use."""
    global _CONFIGURED
    logger = logging.getLogger(_LOGGER_NAME)

    if not _CONFIGURED:
        ensure_app_dir()
        logger.setLevel(logging.INFO)

        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Avoid duplicate handlers if get_logger() is called multiple times.
        if not logger.handlers:
            logger.addHandler(handler)

        logger.propagate = False
        _CONFIGURED = True

    return logger
