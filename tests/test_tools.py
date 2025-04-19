"""Unit‑tests for the three public tools exposed by *CodexMCP*.

The actual *OpenAI Codex* CLI is **not** spawned – we patch the helper that
returns the pipe singleton so that the tools talk to a very small in‑memory
stub returning deterministic payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest


# ---------------------------------------------------------------------------
# Test‑fixture: *StubPipe*
# ---------------------------------------------------------------------------


class _StubPipe:  # pylint: disable=too-few-public-methods
    """Mimics the public surface of :class:`codexMCP.pipe.CodexPipe`."""

    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []

    async def query(self, request: Dict[str, Any], _ctx: Any | None = None) -> Dict[str, Any]:
        """Echo back *request['prompt']* inside the expected Codex JSON shape."""

        self.requests.append(request)

        return {"choices": [{"text": f"ECHO: {request['prompt']}"}]}


import os
import sys
import tempfile


@pytest.fixture()
def stub_pipe(monkeypatch: pytest.MonkeyPatch) -> _StubPipe:  # noqa: D401
    """Patch :func:`codexMCP.pipe.get_pipe` so tools use our stub implementation."""

    # Point the *HOME* environment variable to a temporary, writable location
    # so that ``codexMCP.logging_cfg`` can create its log directory hierarchy
    # without hitting permission errors inside the sandbox.
    tmp_home = tempfile.mkdtemp(prefix="codexmcp‑home‑")
    monkeypatch.setenv("HOME", tmp_home)

    from codexMCP import pipe as _pipe_mod
    from codexMCP import tools as _tools_mod

    stub = _StubPipe()

    # Replace the *get_pipe* helper in **both** the public *pipe* module and
    # the already‑imported *tools* module (the latter holds a direct reference
    # obtained during import‑time).
    monkeypatch.setattr(_pipe_mod, "get_pipe", lambda: stub, raising=True)
    monkeypatch.setattr(_tools_mod, "get_pipe", lambda: stub, raising=True)

    return stub


# ----------------------------------------------------------------------------
# Happy path – the tools should echo back the prompt.
# ----------------------------------------------------------------------------


@pytest.mark.asyncio()
async def test_generate_code_happy(stub_pipe: _StubPipe) -> None:
    from codexMCP.tools import generate_code

    result = await generate_code("prints 'hello'", "Python", model="o4-mini")

    assert result == "ECHO: Write Python code that prints 'hello'."
    assert stub_pipe.requests  # ensure the stub saw the request


@pytest.mark.asyncio()
async def test_refactor_code_happy(stub_pipe: _StubPipe) -> None:
    from codexMCP.tools import refactor_code

    original_code = "print('HELLO')"
    instruction = "lower‑case the greeting"

    expected_prompt_prefix = "Refactor the following code according to the instruction."

    result = await refactor_code(original_code, instruction, model="o4-mini")

    assert result.startswith("ECHO: ")
    assert stub_pipe.requests[-1]["prompt"].startswith(expected_prompt_prefix)


@pytest.mark.asyncio()
async def test_write_tests_happy(stub_pipe: _StubPipe) -> None:
    from codexMCP.tools import write_tests

    snippet = "def add(a, b):\n    return a + b"

    result = await write_tests(snippet)

    assert result.startswith("ECHO: Write tests for the following code.")


# ----------------------------------------------------------------------------
# Error path – malformed JSON should raise *tool_error*.
# ----------------------------------------------------------------------------


class _BadStubPipe(_StubPipe):
    async def query(self, request: Dict[str, Any], _ctx: Any | None = None) -> Dict[str, Any]:
        self.requests.append(request)
        return {"foo": "bar"}  # malformed on purpose


@pytest.mark.asyncio()
@pytest.mark.parametrize("tool_name", ["generate_code", "refactor_code", "write_tests"])
async def test_bad_json_raises(tool_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure *HOME* is writable for logging like in the main fixture.
    tmp_home = tempfile.mkdtemp(prefix="codexmcp‑home‑")
    monkeypatch.setenv("HOME", tmp_home)

    from codexMCP import pipe as _pipe_mod
    from codexMCP import tools as _tools_mod

    monkeypatch.setattr(_pipe_mod, "get_pipe", lambda: _BadStubPipe(), raising=True)
    monkeypatch.setattr(_tools_mod, "get_pipe", lambda: _BadStubPipe(), raising=True)

    tool_func = getattr(_tools_mod, tool_name)

    tool_error = _tools_mod.tool_error  # type: ignore[attr-defined]

    with pytest.raises(tool_error):
        # Provide minimal valid args per signature.
        if tool_name == "generate_code":
            await tool_func("desc")  # type: ignore[arg-type]
        elif tool_name == "refactor_code":
            await tool_func("code", "instruction")  # type: ignore[arg-type]
        else:  # write_tests
            await tool_func("code")


# ----------------------------------------------------------------------------
# The *server* module must be import‑able even without the external SDK.
# ----------------------------------------------------------------------------


def test_server_importable_without_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensures stub fallback for *FastMCP* works when SDK is missing."""

    import importlib, sys as _sys

    monkeypatch.setitem(_sys.modules, "modelcontextprotocol", None)

    import codexMCP.server as server  # noqa: F401 – side‑effect import only

    importlib.reload(server)  # type: ignore[arg-type]
