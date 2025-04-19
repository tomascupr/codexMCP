"""CodexMCP – a lightweight Model Context Protocol (MCP) Server wrapper
around the *OpenAI Codex CLI*.

The public surface of this package is intentionally small; see
``codexMCP.server`` for the executable entry‑point and ``codexMCP.tools`` for
the three user‑facing tools that can be invoked from any MCP‑compatible
client (for example *mcp‑cli* or *Claude Code*).

All logs are written to *~/.codexmcp/logs* – **never** to *stdout* – to avoid
interfering with the framing used by the MCP stdio transport.
"""

from importlib import metadata as _metadata


try:
    __version__: str = _metadata.version(__name__)  # type: ignore[attr-defined]
except _metadata.PackageNotFoundError:  # pragma: no cover – not installed
    __version__ = "0.0.0"


def main() -> None:  # pragma: no cover – thin wrapper
    """Allow ``python -m codexMCP`` as shortcut for ``python -m codexMCP.server``."""

    from .server import main as _run

    _run()
