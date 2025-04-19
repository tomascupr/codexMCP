"""Centralised logging configuration for **CodexMCP**.

Every log record is persisted in ``~/.codexmcp/logs`` – nothing is ever sent
to *stdout* or *stderr* so the Model Context Protocol (MCP) framing handled by
the SDK remains pristine.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


LOG_DIR: Path = Path.home() / ".codexmcp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Global root configuration – modules can simply ``import logging`` and obtain
# a correctly configured logger without doing anything else.
_handler = logging.FileHandler(LOG_DIR / "codexmcp.log")
_handler.setFormatter(logging.Formatter(_FMT))

logging.basicConfig(level=logging.INFO, handlers=[_handler])

# Sub‑modules that want more granularity can still tweak their own loggers –
# this root setup is just the baseline.
