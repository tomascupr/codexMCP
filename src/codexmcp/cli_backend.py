from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import Final, Optional

"""Thin async wrapper around the `codex` CLI binary.

All FastMCP tools route through this module when generating text.  The CLI
has the advantage of automatic local-filesystem context and interactive chain
of thought, so we prefer it over direct OpenAI SDK calls.

If the binary cannot be located, we gracefully fall back to the OpenAI API
at runtime instead of failing at import time.
"""

__all__: Final = ["CodexCLIError", "run", "is_cli_available"]


class CodexCLIError(RuntimeError):
    """Raised when the Codex CLI process exits non-zero or cannot be found."""


# --------------------------------------------------------------------------------------
# Lazy CLI detection - check at runtime, not import time
# --------------------------------------------------------------------------------------
_CODEX_PATH_CACHE: Optional[str] = None
_CLI_CHECKED: bool = False


def _get_codex_path() -> Optional[str]:
    """Get the Codex CLI path, checking only once and caching the result."""
    global _CODEX_PATH_CACHE, _CLI_CHECKED
    
    if not _CLI_CHECKED:
        _CLI_CHECKED = True
        _CODEX_PATH_CACHE = os.getenv("CODEX_PATH") or shutil.which("codex")
    
    return _CODEX_PATH_CACHE


def is_cli_available() -> bool:
    """Check if the Codex CLI is available without raising an error."""
    return _get_codex_path() is not None


DEFAULT_MODEL: Final = os.getenv("CODEX_MODEL", "gpt-4o-mini")


async def run(prompt: str, model: Optional[str] = None) -> str:
    """Execute prompt through Codex CLI and return the completion text.

    Parameters
    ----------
    prompt:
        The user prompt to execute.
    model:
        The model identifier; defaults to environment variable or "gpt-4o-mini".

    Returns
    -------
    str
        The completion text from Codex.
        
    Raises
    ------
    CodexCLIError
        If the CLI is not available or execution fails.
    """
    # Check CLI availability at runtime
    codex_path = _get_codex_path()
    if not codex_path:
        raise CodexCLIError(
            "Codex CLI binary not found in PATH. Install with `npm i -g @openai/codex` ― "
            "see https://github.com/openai/codex#usage for details. "
            "The system will fall back to OpenAI API if available."
        )
    
    mdl = model or DEFAULT_MODEL
    cmd = [
        codex_path,
        "--json",
        "--model",
        mdl,
        "-q",
        prompt,
        "--approval-mode=full-auto",
        "--disable-shell",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="ignore")
        stderr = stderr_bytes.decode("utf-8", errors="ignore")

        if proc.returncode != 0:
            raise CodexCLIError(stderr.strip() or "Codex CLI execution failed")

        if not stdout:
            raise CodexCLIError("No output from Codex CLI")

        # Get the last JSON line from output
        last_line = stdout.strip().split("\n")[-1]
        result = json.loads(last_line)

        # Extract text from any known response format
        for key in ("completion", "text", "response", "content"):
            if key in result:
                content = result[key]

                # Handle list format (seen in "content" responses)
                if (
                    isinstance(content, list)
                    and content
                    and isinstance(content[0], dict)
                ):
                    return content[0].get("text", "").lstrip("\n")

                # Regular string content
                if content:
                    return str(content).lstrip("\n")

        raise CodexCLIError("No completion content found in response")

    except json.JSONDecodeError as exc:
        raise CodexCLIError("Invalid JSON response from Codex CLI") from exc
    except Exception as exc:
        if isinstance(exc, CodexCLIError):
            raise
        raise CodexCLIError(f"CLI execution error: {str(exc)}") from exc
