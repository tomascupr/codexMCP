"""CodexMCP - FastMCP server wrapping the OpenAI Codex CLI."""

from .shared import __version__
from .server import main

__all__ = ["main", "__version__"] 