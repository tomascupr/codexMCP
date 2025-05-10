"""Logging configuration for CodexMCP.

All Codex CLI I/O is recorded to ``~/.codexmcp/logs`` with rotation so that the
files don’t grow indefinitely.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_DIR: Path | None = None


def _ensure_log_dir() -> Path:
    global _LOG_DIR  # noqa: PLW0603

    if _LOG_DIR is not None:
        return _LOG_DIR

    candidate = Path.home() / ".codexmcp" / "logs"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        _LOG_DIR = candidate
    except OSError:
        fallback = Path.cwd() / ".codexmcp.logs"
        fallback.mkdir(parents=True, exist_ok=True)
        _LOG_DIR = fallback

    return _LOG_DIR


def configure_logging(name: str = "codexmcp", console: bool = True) -> logging.Logger:
    log_dir = _ensure_log_dir()
    log_file = log_dir / "codexmcp.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler for persistent logs
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # Console handler for real-time monitoring
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)

    logger.propagate = False

    return logger


logger = configure_logging()


__all__ = ["logger", "configure_logging", "_ensure_log_dir"]
