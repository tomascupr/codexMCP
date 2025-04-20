"""Entry‑point for the *CodexMCP* FastMCP server.

Run via

    python server.py

or as a module once the project root is on *PYTHONPATH*.

The server exposes three tools – *generate_code*, *refactor_code* and
*write_tests* – over *stdio* for use with *mcp‑cli* and compatible clients.
"""

from __future__ import annotations

import os
import sys

# Ensure logging is configured early (could also be in shared.py)
from logging_cfg import logger  # noqa: F401 – ensure logging is configured first.

# Import shared singletons
from shared import mcp, pipe  # <-- Import from shared.py

# Remove direct FastMCP and CodexPipe imports if no longer needed here
# from fastmcp import FastMCP
# from pipe import CodexPipe

# Add current directory to path for reliable module discovery
# _PROJECT_ROOT = os.path.dirname(__file__) or "."
# sys.path.insert(0, _PROJECT_ROOT) # Moved to shared.py

# Remove the singleton definitions and initialization logic from here
# ---------------------------------------------------------------------------
# Shared singletons ...
# ---------------------------------------------------------------------------
# mcp = FastMCP("CodexMCP")
# pipe: CodexPipe | None = None
# CODEX_CMD = [...]
# os.environ[...] = ...
# try: ... pipe = CodexPipe(...) ... except ... # All moved to shared.py

def _ensure_event_loop_policy() -> None:
    """On Windows the *ProactorEventLoop* is mandatory for subprocess pipes."""

    if os.name == "nt":
        import asyncio

        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):  # type: ignore[attr-defined]
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore[attr-defined]

def main() -> None:
    """Main entry point for the CodexMCP server."""
    _ensure_event_loop_policy()
    logger.info("CodexMCP server starting … PID=%s", os.getpid())

    # Check if pipe initialized successfully (imported from shared.py)
    if pipe is None:
        logger.error("Shared CodexPipe failed to initialize. Server cannot start.")
        sys.exit(1)

    try:
        # Import tools here, which will now import mcp/pipe from shared.py
        logger.info("Importing tools module...")
        import tools  # noqa: F401 pylint: disable=unused-import,import-outside-toplevel
        logger.info("Tools module imported successfully.")

        # Optional: Log registered tools after import
        try:
            # Need asyncio loop to run get_tools, log confirms import success for now
            # tools_dict = asyncio.run(mcp.get_tools()) # Avoid asyncio.run here
            # logger.info("Registered tools check (requires running loop): %s", list(tools_dict.keys()))
            pass
        except Exception as e_get_tools:
             logger.error("Failed during tool check phase: %s", str(e_get_tools), exc_info=True)

        logger.info("Starting FastMCP server run loop...")
        mcp.run() # This starts the server and event loop
        logger.info("FastMCP server run loop finished.")

    except ImportError as e_import:
        logger.error("Failed to import tools module: %s", e_import, exc_info=True)
        sys.exit(1)
    except Exception as e_main:
        logger.error("Error in server main execution: %s", str(e_main), exc_info=True)
        sys.exit(1)
    finally:
        logger.info("CodexMCP server shutting down.")

if __name__ == "__main__":
    main()
