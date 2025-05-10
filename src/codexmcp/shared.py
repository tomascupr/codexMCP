"""Shared singletons (mcp, pipe, config) for CodexMCP."""

from __future__ import annotations

import os
import sys
from dotenv import load_dotenv
from fastmcp import FastMCP
from .logging_cfg import configure_logging
from .client import LLMClient

# Add project root to path early for imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) or "."
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables from .env file first
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

# Configure logging with console output based on environment variable
console_logging = os.environ.get("CODEXMCP_CONSOLE_LOG", "1").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
logger = configure_logging(console=console_logging)

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------

logger.info("Initializing shared MCP instance...")
mcp = FastMCP("CodexMCP")
logger.info("Shared MCP instance initialized.")

# Patch in a compatibility helper if FastMCP lacks get_tool_schemas
if not hasattr(mcp, "get_tool_schemas") or not callable(
    getattr(mcp, "get_tool_schemas", None)
):

    def _get_tool_schemas() -> list[dict]:
        """Return a minimal list of tool schema dicts with at least a *name* key.

        This falls back to introspection of common FastMCP internal attributes
        (``mcp._tools`` or ``mcp.tools``). Only the *name* field is guaranteed
        because that is all *server.py* currently relies on for logging.
        """

        schemas: list[dict] = []

        # Try internal mapping attributes that are commonly used by FastMCP
        for attr_name in ("_tools", "tools"):
            tools_attr = getattr(mcp, attr_name, None)
            if not tools_attr:
                continue

            # Dictionaries map *name -> Tool* instances
            if isinstance(tools_attr, dict):
                for name in tools_attr.keys():
                    schemas.append({"name": name})

            # Lists may hold Tool objects with a ``name`` attribute
            elif isinstance(tools_attr, list):
                for tool in tools_attr:
                    tool_name = getattr(tool, "name", None) or getattr(
                        tool, "__name__", None
                    )
                    if tool_name:
                        schemas.append({"name": tool_name})

            # Stop early if we found any schemas
            if schemas:
                break

        # If no tools found via introspection, just return our known tools
        if not schemas:
            # These are the tools we know exist in our codebase
            known_tools = ["code_generate", "describe_codebase", "review_code"]
            for name in known_tools:
                schemas.append({"name": name})

        return schemas

    # Attach the helper to the MCP instance
    setattr(mcp, "get_tool_schemas", _get_tool_schemas)

    logger.debug("Injected fallback mcp.get_tool_schemas() helper for compatibility.")

# Pre-initialize client
client = LLMClient()
logger.info("Initialized LLM client")

# CodexPipe support removed – CLI is executed per-call in `cli_backend`.

__version__ = "0.1.6"
