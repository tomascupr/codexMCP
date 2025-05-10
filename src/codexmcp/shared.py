"""Shared singletons (mcp, pipe, config) for CodexMCP."""

from __future__ import annotations

import os
import sys

# Add project root to path early for imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) or "."
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables from .env file first
from dotenv import load_dotenv

# Try loading .env from current working directory first, then package directory
_dotenv_paths = [
    os.path.join(os.getcwd(), ".env"),  # Current working directory
    os.path.join(_PROJECT_ROOT, ".env"),  # Project root
]

_env_loaded = False
for _dotenv_path in _dotenv_paths:
    if os.path.exists(_dotenv_path):
        load_dotenv(dotenv_path=_dotenv_path)
        print(f"Loaded .env file from: {_dotenv_path}")
        _env_loaded = True
        break

if not _env_loaded:
    print("Warning: No .env file found in current directory or project root")

from fastmcp import FastMCP
from .logging_cfg import configure_logging

# Configure logging with console output based on environment variable
console_logging = os.environ.get("CODEXMCP_CONSOLE_LOG", "1").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
logger = configure_logging(console=console_logging)

# Import config

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------

logger.info("Initializing shared MCP instance...")
mcp = FastMCP("CodexMCP")
logger.info("Shared MCP instance initialized.")

# Import components after config is initialized
from .client import LLMClient

# Pre-initialize client
client = LLMClient()
logger.info("Initialized LLM client")

# CodexPipe support removed – CLI is executed per-call in `cli_backend`.

__version__ = "0.1.5"
