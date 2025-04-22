"""Entry‑point for the *CodexMCP* FastMCP server.

Run via

    python server.py

or as a module once the project root is on *PYTHONPATH*.

The server exposes tools like *generate_code*, *refactor_code*, *write_tests*,
*explain_code*, and *generate_docs* over *stdio* for use with *mcp‑cli* and compatible clients.

You can enable console logging by setting the CODEXMCP_CONSOLE_LOG environment variable to "1".
"""

from __future__ import annotations

import os
import sys

# Configure logging based on environment variable
console_logging = os.environ.get("CODEXMCP_CONSOLE_LOG", "1").lower() in ("1", "true", "yes", "on")

# Ensure logging is configured early with console output if enabled
from .logging_cfg import configure_logging
logger = configure_logging(console=console_logging)

# Import shared singletons
from .shared import mcp, pipe  # <-- Import from shared.py

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
    logger.info("=== CodexMCP Server Starting === PID=%s ===", os.getpid())
    logger.info("Console logging is %s", "ENABLED" if console_logging else "DISABLED")

    # Check if pipe initialized successfully (imported from shared.py)
    if pipe is None:
        logger.error("Shared CodexPipe failed to initialize. Server cannot start.")
        sys.exit(1)

    try:
        # Import tools here, which will now import mcp/pipe from shared.py
        logger.info("Importing tools module...")
        from . import tools  # noqa: F401 pylint: disable=unused-import,import-outside-toplevel
        logger.info("Tools module imported successfully.")

        # Log available tools
        tool_names = [
            "generate_code", "refactor_code", "write_tests", 
            "explain_code", "generate_docs"
        ]
        logger.info("Available tools: %s", ", ".join(tool_names))
        
        logger.info("Server is ready to process requests.")
        logger.info("=== Starting FastMCP Server Loop ===")
        
        # This starts the server and event loop
        mcp.run()
        
        logger.info("=== FastMCP Server Loop Finished ===")

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
