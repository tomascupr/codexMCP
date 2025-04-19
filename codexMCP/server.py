"""Executable entry‑point for **CodexMCP**.

It instantiates the *FastMCP* runtime, registers the tools found in
``codexMCP.tools`` and then hands control over to the MCP event‑loop running
on *stdio*.

The module purposefully does **not** import ``codexMCP.pipe`` – the first tool
invocation will spin‑up the underlying Codex CLI on‑demand. This keeps the
start‑up time small (<2 s) which is a requirement of the specification.
"""

from __future__ import annotations

import asyncio
import logging

# Ensure logs are configured before anything else.
from . import logging_cfg  # noqa: F401  # pylint: disable=unused-import


# The MCP SDK might not be present in the local environment when developers
# import this module for documentation or linting. Fallback to a tiny stub so
# the import succeeds outside of the production runtime.
try:
    from modelcontextprotocol import FastMCP  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – offline test environment

    class _StubMCP:  # pylint: disable=too-few-public-methods
        def __init__(self, _name: str):
            self.name = _name

        def register_tools_module(self, _mod):
            return None

        async def run(self):  # noqa: D401
            raise RuntimeError("FastMCP stub cannot run – install modelcontextprotocol>=0.6")

    FastMCP = _StubMCP  # type: ignore  # noqa: N816


async def _amain() -> None:
    """Build the MCP server instance and start serving."""

    server = FastMCP("CodexMCP")

    # The tools are dynamically discovered by the SDK once we import the module.
    from . import tools  # noqa: F401 – imported for side‑effects

    server.register_tools_module(tools)  # type: ignore[attr-defined]

    logging.getLogger(__name__).info("CodexMCP server initialised – awaiting MCP client …")

    await server.run()  # type: ignore[attr-defined]


def main() -> None:  # pragma: no cover
    """Synchronous wrapper so we can ``python -m codexMCP.server``."""

    asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover – executed when run as script
    main()
