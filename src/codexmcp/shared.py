"""Shared singletons (mcp, pipe, config) for CodexMCP."""

from __future__ import annotations

import os
import sys
import shutil  # Import shutil

# Add project root to path early for imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) or "."
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables from .env file first
from dotenv import load_dotenv

# Try loading .env from current working directory first, then package directory
_dotenv_paths = [
    os.path.join(os.getcwd(), '.env'),  # Current working directory
    os.path.join(_PROJECT_ROOT, '.env'),  # Project root
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
from .pipe import CodexPipe

# Configure logging with console output based on environment variable
console_logging = os.environ.get("CODEXMCP_CONSOLE_LOG", "1").lower() in ("1", "true", "yes", "on")
logger = configure_logging(console=console_logging)

# Import config
from .config import config

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------

logger.info("Initializing shared MCP instance...")
mcp = FastMCP("CodexMCP")
logger.info("Shared MCP instance initialized.")

# Import components after config is initialized
from .client import LLMClient
from .prompts import prompts

# Pre-initialize client
client = LLMClient()
logger.info("Initialized LLM client")

pipe: CodexPipe | None = None

# -----------------------------------------------------------
# Codex CLI detection
# -----------------------------------------------------------

# Locate `codex` executable.  If it is unavailable we fall back to
# using the LLMClient directly.

codex_executable_path = shutil.which("codex")

if not codex_executable_path:
    logger.warning(
        "'codex' executable not found – Codex CLI features disabled. "
        "The library will use the LLM Client API interface instead."
    )
    CODEX_CMD = None  # CodexPipe will not be initialised
else:
    logger.info(f"Found 'codex' executable at: {codex_executable_path}")
    CODEX_CMD = [
        codex_executable_path,
        "--json",
        "--pipe",
        "-q",
        "Hello",  # initial dummy prompt to satisfy quiet mode
        "--approval-mode=full-auto",
        "--disable-shell",
        "--exit-when-idle",
    ]

# Set environment variable before creating the pipe
os.environ["CODEX_ALLOW_DIRTY"] = "1"

# Initialize CodexPipe only if the command was found and CLI usage is enabled
if CODEX_CMD and os.environ.get("CODEXMCP_USE_CLI", "1").lower() in ("1", "true", "yes"):
    try:
        logger.info("Initializing shared CodexPipe instance...")
        pipe = CodexPipe(CODEX_CMD)
        logger.info("Shared CodexPipe instance initialized.")
        # Discard the first response
        logger.info("Attempting to discard dummy prompt response...")
        try:
            # Consider making this non-blocking if it causes startup delays
            _ = pipe.process.stdout.readline()
            logger.info("Dummy prompt response discarded.")
        except Exception as e_read:
            logger.warning(f"Could not read/discard dummy prompt response: {e_read}")
    except Exception as e_pipe:  # Catch generic exceptions during pipe init
        logger.error(f"Failed to initialize CodexPipe with command '{' '.join(CODEX_CMD)}': {e_pipe}", exc_info=True)
        pipe = None  # Ensure pipe is None if initialization fails
else:
    # Logged the error earlier when codex_executable_path was None
    logger.info("CodexPipe not initialized. Using LLM client exclusively.")
    pipe = None

__version__ = "0.1.5"
