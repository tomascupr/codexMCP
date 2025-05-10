"""Entry‑point for the *CodexMCP* FastMCP server.

Run via

    python server.py

or as a module once the project root is on *PYTHONPATH*.

The server exposes tools like *generate_code*, *refactor_code*, *write_tests*,
*explain_code*, and *generate_docs* over *stdio* for use with *mcp‑cli* and compatible clients.

You can enable console logging by setting the CODEXMCP_CONSOLE_LOG environment variable to "1".
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------
# Server script that exposes FastMCP/CodexMCP tools over JSON-RPC.
# --------------------------------------------------------------------------------------

import os
import sys
from .logging_cfg import configure_logging
from .shared import mcp  # MCP instance (CodexPipe no longer required)

# Ensure early expansion of sys.path to include the package root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) or "."
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Determine console logging from environment
console_logging = os.environ.get("CODEXMCP_CONSOLE_LOG", "1").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

# Initialize logger
logger = configure_logging(console=console_logging)


def _ensure_event_loop_policy() -> None:
    """On Windows the *ProactorEventLoop* is mandatory for subprocess pipes."""

    if os.name == "nt":
        import asyncio

        if not isinstance(
            asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
        ):  # type: ignore[attr-defined]
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore[attr-defined]


def main() -> None:
    """Main entry point for the CodexMCP server."""
    _ensure_event_loop_policy()
    logger.info("=== CodexMCP Server (v0.1.6) Starting === PID=%s ===", os.getpid())
    logger.info("Console logging is %s", "ENABLED" if console_logging else "DISABLED")

    try:
        # Import tools here, which will now import mcp/pipe from shared.py
        logger.info("Importing tools module...")
        import importlib

        importlib.import_module(f"{__package__}.tools")
        logger.info("Tools module imported successfully.")

        # Log available tools
        tool_names = ["Error: Could not determine tool list"]  # Default
        if hasattr(mcp, "get_tool_schemas") and callable(mcp.get_tool_schemas):
            try:
                schemas = mcp.get_tool_schemas()  # Assuming this is the method
                if isinstance(schemas, list):
                    # Ensure names are extracted correctly and filter out None or empty names
                    valid_names = []
                    for s in schemas:
                        if isinstance(s, dict) and "name" in s and s["name"]:
                            valid_names.append(s["name"])
                    if valid_names:  # Only update if we got some valid names
                        tool_names = valid_names
                    elif schemas:  # Schemas list was not empty but no valid names found
                        logger.warning(
                            "mcp.get_tool_schemas() returned schemas, but no valid 'name' keys found in them."
                        )
                    else:  # Schemas list was empty
                        logger.info("mcp.get_tool_schemas() returned an empty list.")
                        tool_names = []  # Explicitly set to empty list of names
                else:
                    logger.warning(
                        f"mcp.get_tool_schemas() did not return a list, but: {type(schemas)}"
                    )
            except Exception as e:
                logger.error(
                    f"Error calling mcp.get_tool_schemas(): {e}", exc_info=True
                )
        else:
            logger.error(
                "mcp object does not have a callable get_tool_schemas() method."
            )

        if (
            not tool_names and tool_names != []
        ):  # Handles the default error message case if it wasn't overwritten by an empty list
            logger.warning(
                "Tool list could not be determined. Server might not have tools registered or there's an issue fetching them."
            )
        elif not tool_names:  # Specifically for an empty list of tools
            logger.info("No tools are currently registered or listed by the server.")
        else:
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
