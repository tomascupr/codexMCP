"""Shared singletons (mcp, pipe) for CodexMCP."""

from __future__ import annotations

import os
import sys

# Add project root to path early for imports
_PROJECT_ROOT = os.path.dirname(__file__) or "."
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables from .env file first
from dotenv import load_dotenv

# Construct the absolute path to the .env file
_dotenv_path = os.path.join(_PROJECT_ROOT, '.env')

# Load the .env file if it exists
if os.path.exists(_dotenv_path):
    load_dotenv(dotenv_path=_dotenv_path)
    print(f"Loaded .env file from: {_dotenv_path}") # Add print statement
else:
    print(f".env file not found at: {_dotenv_path}") # Add print statement

from fastmcp import FastMCP
from logging_cfg import logger # Import logger here as well
from pipe import CodexPipe

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------

logger.info("Initializing shared MCP instance...")
mcp = FastMCP("CodexMCP")
logger.info("Shared MCP instance initialized.")

pipe: CodexPipe | None = None

CODEX_CMD = [
    "codex",
    "--json",
    "--pipe",
    "-q", "Hello",  # initial dummy prompt to satisfy quiet mode
    "--approval-mode=full-auto",
    "--disable-shell",
]

# Set environment variable before creating the pipe
os.environ["CODEX_ALLOW_DIRTY"] = "1"
# OPENAI_API_KEY is handled within CodexPipe initialization in pipe.py

try:
    logger.info("Initializing shared CodexPipe instance...")
    pipe = CodexPipe(CODEX_CMD)
    logger.info("Shared CodexPipe instance initialized.")
    # Discard the first response
    logger.info("Attempting to discard dummy prompt response in shared...")
    try:
        # Consider making this non-blocking if it causes startup delays
        _ = pipe.process.stdout.readline()
        logger.info("Dummy prompt response discarded in shared.")
    except Exception as e_read:
        logger.warning("Could not read/discard dummy prompt response in shared: %s", e_read)
except FileNotFoundError:
    logger.error(
        "Error: 'codex' executable not found in shared.py. Install via 'npm i -g @openai/codex' and ensure it is on $PATH.",
        exc_info=True
    )
    pipe = None # Ensure pipe is None if initialization fails
except Exception as e_pipe:
    logger.error("Failed to initialize shared CodexPipe: %s", e_pipe, exc_info=True)
    pipe = None # Ensure pipe is None if initialization fails

__version__ = "0.1.0" 