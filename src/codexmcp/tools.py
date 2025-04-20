"""FastMCP tools exposed by *CodexMCP*."""

from __future__ import annotations

import json
from typing import Any

from fastmcp import Context, exceptions

from .logging_cfg import logger
from .shared import mcp, pipe


async def _query_codex(ctx: Context, prompt: str, *, model: str = "o4-mini") -> str:
    if pipe is None:
        raise exceptions.ToolError("CodexPipe is not initialized. Cannot query Codex.")

    request = {"prompt": prompt, "model": model}

    await pipe.send(request)

    try:
        raw = await pipe.recv(progress_cb=getattr(ctx, "progress", None))
        response: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to decode Codex JSON: %s", raw)
        raise exceptions.ToolError("Codex returned invalid JSON.") from exc

    for key in ("completion", "text", "response"):
        if key in response:
            return str(response[key]).lstrip("\n")

    logger.error("Unexpected Codex response: %s", response)
    raise exceptions.ToolError("Codex response missing `completion` field.")


@mcp.tool()
async def generate_code(ctx: Context, description: str, language: str = "Python", model: str = "o4-mini") -> str:
    """Generate *language* source code that fulfils *description*."""

    prompt = (
        f"# Task\nGenerate {language} code that fulfils the following requirement:\n"
        f"{description}\n\n# Provide only the source code without explanations."
    )

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def refactor_code(ctx: Context, code: str, instruction: str, model: str = "o4-mini") -> str:
    """Refactor *code* as per *instruction*."""

    prompt = (
        "# Original code\n" + code.strip() + "\n\n" +
        "# Refactor instruction\n" + instruction.strip() + "\n\n" +
        "# Refactored code (output only the code)"
    )

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_tests(ctx: Context, code: str, description: str = "", model: str = "o4-mini") -> str:
    """Generate unit tests for *code*."""

    prompt = (
        "# Code under test\n" + code.strip() + "\n\n" +
        (f"# Additional context\n{description}\n\n" if description else "") +
        "# Write thorough unit tests in the same language. Return only the test code."
    )

    return await _query_codex(ctx, prompt, model=model)
