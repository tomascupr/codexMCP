from __future__ import annotations

"""Thin async wrapper around the `codex` CLI binary.

All FastMCP tools route through this module when generating text.  The CLI
has the advantage of automatic local-filesystem context and interactive chain
of thought, so we prefer it over direct OpenAI SDK calls.

If the binary cannot be located we fail fast at **import time** so the user is
instructed to install it explicitly.

This keeps the rest of the codebase simple: one import and one function
(`run`) replaces the former multi-backend logic.
"""

import asyncio
import json
import os
import shutil
from typing import Final, Optional

from .logging_cfg import logger

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
    """Execute *prompt* through Codex CLI and return the final completion text.

    Parameters
    ----------
    prompt:
        The user prompt to pass after `-q`.
    model:
        The model identifier; defaults to ``CODEX_MODEL`` env or ``gpt-4o-mini``.

    Returns
    -------
    str
        The completion string extracted from the last JSON line that Codex
        emits with status *completed*.
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

    logger.debug("Running Codex CLI: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_bytes, stderr_bytes = await proc.communicate()
    stdout = stdout_bytes.decode('utf-8', errors='ignore')
    stderr = stderr_bytes.decode('utf-8', errors='ignore')

    if proc.returncode != 0:
        raise CodexCLIError(stderr.strip() or "Codex CLI exited with non-zero status")

    if not stdout:
        raise CodexCLIError("Codex CLI produced no output")

    # Codex emits a stream of JSON lines; grab the last one.
    last_line = stdout.strip().split("\n")[-1]
    try:
        payload = json.loads(last_line)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Codex JSON: %s", exc, exc_info=True)
        raise CodexCLIError("Invalid JSON from Codex CLI") from exc

    # Various keys have been observed (completion, text, response, content).
    for key in ("completion", "text", "response", "content"):
        if key in payload and payload[key]:
            if key == "content" and isinstance(payload[key], list):
                # content may be list[ {text: "..."} ]
                first = payload[key][0]
                return (first.get("text", "") if isinstance(first, dict) else str(first)).lstrip("\n")
            return str(payload[key]).lstrip("\n")

    raise CodexCLIError("Codex CLI JSON did not contain a completion field") 