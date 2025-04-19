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

from fastmcp import FastMCP

from logging_cfg import logger  # noqa: F401 – ensure logging is configured first.
from pipe import CodexPipe

# ---------------------------------------------------------------------------
# Shared singletons – created exactly once so that the same instances are used
# across all imported modules.
# ---------------------------------------------------------------------------

mcp = FastMCP("CodexMCP")

CODEX_CMD = [
    "codex",
    "--json",
    "--pipe",
    "--approval-mode=full-auto",
    "--disable-shell",
]


try:
    pipe = CodexPipe(CODEX_CMD)
except FileNotFoundError:
    print(
        "Error: 'codex' executable not found – install via 'npm i -g @openai/codex' and ensure it is on $PATH.",
        file=sys.stderr,
    )
    raise

# Late import so tools can access the already‑instantiated *mcp* and *pipe*.
import tools  # noqa: E402  pylint: disable=wrong-import-position,unused-import


def _ensure_event_loop_policy() -> None:
    """On Windows the *ProactorEventLoop* is mandatory for subprocess pipes."""

    if os.name == "nt":
        import asyncio

        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):  # type: ignore[attr-defined]
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore[attr-defined]


if __name__ == "__main__":
    _ensure_event_loop_policy()
    logger.info("CodexMCP server starting … PID=%s", os.getpid())
    try:
        mcp.run()
    finally:
        logger.info("CodexMCP server shutting down.")
