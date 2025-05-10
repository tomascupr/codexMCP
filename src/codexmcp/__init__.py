"""CodexMCP - FastMCP server wrapping the OpenAI Codex CLI."""

from .shared import __version__
# Remove direct import of main from .server to avoid premature loading
# from .server import main

# If 'main' needs to be exportable from the package top-level,
# it could be dynamically imported, or users directed to use python -m.
# For now, we'll rely on `python -m codexmcp.server` as the primary way to run.

__all__ = ["__version__"]  # "main" is removed as it's not directly imported
