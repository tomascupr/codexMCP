"""The three public tools exposed by *CodexMCP*.

They are kept intentionally thin – all heavy lifting is delegated to the
persistent *CodexPipe* instance so that latency remains low once the first
request spun‑up the underlying Codex CLI process.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from .pipe import get_pipe

# Import the MCP SDK – during unit tests the real dependency might not be
# available so we fall back to a *very* small shim that provides the symbols
# we actually need (``tool`` decorator, ``tool_error`` exception class and a
# dummy ``Context`` with a *progress()* coroutine method).

try:
    from modelcontextprotocol import tool, tool_error  # type: ignore
    from modelcontextprotocol._types import Context  # type: ignore

except ModuleNotFoundError:  # pragma: no cover – offline test environment

    def tool(*_dargs: Any, **_dkwargs: Any):  # type: ignore
        """Very small no‑op replacement for the real *@mcp.tool* decorator."""

        def _decorator(func):
            return func

        return _decorator

    class tool_error(RuntimeError):
        """Stubbed exception mirroring *mcp.tool_error* behaviour."""

    class _DummyCtx:  # pylint: disable=too-few-public-methods
        async def progress(self, _msg: str) -> None:  # noqa: D401
            return None

    Context = _DummyCtx  # type: ignore  # noqa: N816 – align with SDK naming


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _raise_on_bad_json(obj: Dict[str, Any]) -> None:
    """Validate *obj* matches the shape returned by the Codex CLI."""

    try:
        assert "choices" in obj and obj["choices"], "missing choices"
        assert "text" in obj["choices"][0], "missing text field"
    except AssertionError as exc:  # pragma: no cover – should never happen
        raise tool_error(str(exc)) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool()
async def generate_code(
    description: str,
    language: str = "Python",
    model: str = "o4-mini",
    *,
    ctx: Context | None = None,
) -> str:
    """Generate *language* code that satisfies *description*."""

    prompt = f"Write {language} code that {description}."

    response_json = await get_pipe().query({"prompt": prompt, "model": model}, ctx)

    _raise_on_bad_json(response_json)

    return response_json["choices"][0]["text"].strip()


@tool()
async def refactor_code(
    code: str,
    instruction: str,
    model: str = "o4-mini",
    *,
    ctx: Context | None = None,
) -> str:
    """Apply *instruction* to *code* and return the refactored version."""

    prompt = (
        "Refactor the following code according to the instruction.\n\n"
        f"Instruction: {instruction}\n\n"
        "Code:\n"
        f"{code}\n\nRefactored code:"
    )

    response_json = await get_pipe().query({"prompt": prompt, "model": model}, ctx)

    _raise_on_bad_json(response_json)

    return response_json["choices"][0]["text"].strip()


@tool()
async def write_tests(
    code: str,
    description: str = "",
    model: str = "o4-mini",
    *,
    ctx: Context | None = None,
) -> str:
    """Generate tests for *code* optionally guided by an extra *description*."""

    prompt = (
        "Write tests for the following code.\n\n"
        f"{code}\n\n"
    )
    if description:
        prompt += f"Additional context: {description}\n"

    response_json = await get_pipe().query({"prompt": prompt, "model": model}, ctx)

    _raise_on_bad_json(response_json)

    return response_json["choices"][0]["text"].strip()
