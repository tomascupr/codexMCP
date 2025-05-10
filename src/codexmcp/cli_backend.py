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

If the binary cannot be located we fail fast at **import time** so the user is
instructed to install it explicitly.

This keeps the rest of the codebase simple: one import and one function
(`run`) replaces the former multi-backend logic.
"""

__all__: Final = ["CodexCLIError", "run"]


class CodexCLIError(RuntimeError):
    """Raised when the Codex CLI process exits non-zero or cannot be found."""


# --------------------------------------------------------------------------------------
# Locate the binary once — fail fast if missing.
# --------------------------------------------------------------------------------------
CODEX_PATH: Final = os.getenv("CODEX_PATH") or shutil.which("codex")
if not CODEX_PATH:
    raise CodexCLIError(
        "Codex CLI binary not found in PATH. Install with `npm i -g @openai/codex` ― "
        "see https://github.com/openai/codex#usage for details."
    )

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
    """
    mdl = model or DEFAULT_MODEL
    cmd = [
        CODEX_PATH,
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
