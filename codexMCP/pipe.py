"""Asynchronous wrapper around the *OpenAI Codex CLI* ``--pipe`` mode.

The CLI is spawned exactly once and kept alive for the whole life‑time of the
process so successive tool invocations incur minimal latency.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the global logging configuration is loaded *early*.
from . import logging_cfg  # noqa: F401  # pylint: disable=unused-import


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")


class CodexPipe:
    """Maintains a persistent *codex* subprocess in ``--pipe`` mode."""

    _CMD = [
        "codex",
        "--json",
        "--pipe",
        "--approval-mode=full-auto",
        "--disable-shell",
    ]

    def __init__(self) -> None:
        self._logger = logging.getLogger("codexMCP.pipe")
        self._process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._stderr_task: Optional[asyncio.Task[None]] = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    async def query(self, request: Dict[str, Any], ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Send *request* JSON to Codex and return the parsed JSON response.

        Parameters
        ----------
        request: Dict[str, Any]
            A JSON‑serialisable payload understood by the Codex CLI. At the
            very least it must include a ``prompt`` and a ``model`` key.
        ctx: Optional[mcp.Context]
            The *tool context* injected by the MCP runtime. When provided, the
            function emits a *still working* progress message every ~10s of
            silence from the Codex subprocess.
        """

        await self._ensure_started()

        assert self._process is not None  # mypy – after ensure_started()

        async with self._lock:  # guarantee request/response ordering
            payload = json.dumps(request, ensure_ascii=False)
            self._logger.debug("SEND ▶ %s", payload)

            self._process.stdin.write(payload.encode("utf‑8") + b"\n")  # type: ignore[arg-type]
            await self._process.stdin.drain()

            response_line: Optional[str] = None
            last_progress = time.monotonic()

            while True:
                try:
                    raw = await asyncio.wait_for(self._process.stdout.readline(), timeout=2.0)
                except asyncio.TimeoutError:
                    # Emit progress every 10 seconds of silence.
                    if ctx is not None and time.monotonic() - last_progress >= 10.0:
                        # The MCP SDK expects *await*able progress calls.
                        try:
                            await ctx.progress("still working")  # type: ignore[attr-defined]
                        except Exception:  # pragma: no cover – SDK problems should not crash us
                            pass
                        last_progress = time.monotonic()
                    continue

                if not raw:  # EOF – Codex crashed
                    raise RuntimeError("Codex CLI closed unexpectedly whilst waiting for a response")

                line = raw.decode("utf‑8", errors="replace").strip()
                if not line:
                    continue  # skip empty lines

                self._logger.debug("RECV ◀ %s", line)

                # The Codex CLI might interleave non‑JSON information on *stdout*.
                try:
                    response = json.loads(line)
                except json.JSONDecodeError:
                    # Not JSON – ignore.
                    continue

                return response  # Parsed successfully – we're done.

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_started(self) -> None:
        """Spawn the Codex CLI if it is not running yet."""

        if self._process is not None and self._process.returncode is None:
            return  # already running

        self._logger.info("Starting Codex CLI: %s", " ".join(self._CMD))

        env = os.environ.copy()
        if "OPENAI_API_KEY" not in env:
            self._logger.warning("Environment variable OPENAI_API_KEY not set – Codex will most likely fail")

        self._process = await asyncio.create_subprocess_exec(
            *self._CMD,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Start a background task draining *stderr* so the buffer never fills.
        self._stderr_task = asyncio.create_task(self._drain_stderr(), name="codexMCP.stderr")

    async def _drain_stderr(self) -> None:
        assert self._process is not None  # mypy guard

        while True:
            if self._process.stderr is None:
                break

            data = await self._process.stderr.readline()
            if not data:
                break  # process ended

            text = _ANSI_RE.sub("", data.decode("utf‑8", errors="replace").rstrip())
            logging.getLogger("codexMCP.pipe.stderr").debug(text)


_PIPE: Optional[CodexPipe] = None


def get_pipe() -> CodexPipe:
    """Return a *module‑level* singleton instance of :class:`CodexPipe`."""

    global _PIPE  # noqa: PLW0603 – singleton pattern

    if _PIPE is None:
        _PIPE = CodexPipe()
    return _PIPE
