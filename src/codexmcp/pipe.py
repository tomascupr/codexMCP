"""Async wrapper around a *Codex CLI* subprocess.

The CLI is started in *pipe* mode so that it accepts JSON requests on *stdin*
and emits JSON responses on *stdout*.  This module provides thin `async`
wrappers so that the rest of the application can remain fully asynchronous.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from subprocess import PIPE, Popen
from typing import Any, Callable, Optional

from .logging_cfg import logger

# Strip ANSI escape sequences.
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")

ProgressCallback = Callable[[str], None]


class CodexPipe:
    """Maintain a long‑lived Codex CLI subprocess."""

    def __init__(self, cmd: list[str]):
        logger.info("Starting Codex CLI: %s", " ".join(cmd))

        # Set CI=true environment variable to potentially avoid UI crashes
        popen_env = os.environ.copy()
        popen_env['CI'] = 'true'
        
        # Remove explicit OPENAI_API_KEY handling - should be inherited via os.environ now
        # if 'OPENAI_API_KEY' in os.environ:
        #     logger.info("Passing OPENAI_API_KEY to Codex subprocess environment.")
        #     popen_env['OPENAI_API_KEY'] = os.environ['OPENAI_API_KEY']
        # else:
        #     logger.warning("OPENAI_API_KEY not found in environment for Codex subprocess.")

        logger.info("Starting Popen, inheriting environment.")
        self.process: Popen[str] = Popen(
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            bufsize=1,
            env=popen_env,
        )
        logger.info("Popen process started for Codex CLI.")

        if not self.process.stdin or not self.process.stdout or not self.process.stderr:
            raise RuntimeError("Failed to open Codex subprocess pipes.")

        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

        self._write_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def send(self, message: dict[str, Any]) -> None:
        data = json.dumps(message, ensure_ascii=False)
        logger.info("→ SENDING REQUEST: %s", data)

        async with self._write_lock:
            await asyncio.to_thread(self._write, data)

    async def recv(
        self,
        progress_cb: Optional[ProgressCallback] = None,
        silent_timeout: float = 10.0,
    ) -> str:
        async def _readline() -> str:
            return await asyncio.to_thread(self.process.stdout.readline)  # type: ignore[arg-type]

        while True:
            try:
                line = await asyncio.wait_for(_readline(), timeout=silent_timeout)
            except asyncio.TimeoutError:
                if progress_cb:
                    try:
                        progress_cb("still working")
                    except Exception:
                        logger.exception("Progress callback failed.")
                continue

            if line == "":
                logger.error("Codex subprocess terminated unexpectedly.")
                raise RuntimeError("Codex subprocess terminated unexpectedly.")

            line = line.rstrip("\n")
            if not line.strip():
                continue

            logger.info("← RECEIVED RESPONSE: %s", line)
            return line

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write(self, data: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(data + "\n")
        self.process.stdin.flush()

    def _drain_stderr(self) -> None:
        assert self.process.stderr is not None
        for raw in self.process.stderr:
            line = ANSI_RE.sub("", raw.rstrip("\n"))
            if line:
                logger.info("stderr: %s", line)

    # ------------------------------------------------------------------
    async def aclose(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            await asyncio.to_thread(self.process.wait, timeout=5)

    async def __aenter__(self) -> "CodexPipe":
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        await self.aclose()
        return None


__all__ = ["CodexPipe"]
