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
    logger.info("TOOL REQUEST: generate_code - language=%s, model=%s", language, model)

    prompt = (
        f"# Task: Code Generation\n"
        f"You are an expert {language} developer tasked with implementing the following:\n\n"
        f"## Requirements\n{description}\n\n"
        f"## Guidelines\n"
        f"- Focus on readability, efficiency, and best practices for {language}\n"
        f"- Include appropriate error handling\n"
        f"- Use descriptive variable/function names\n"
        f"- Follow established {language} conventions and idioms\n"
        f"- Write maintainable, well-structured code\n\n"
        f"## Output Format\n"
        f"Provide only the source code without explanations or comments beyond what's necessary for code documentation."
    )

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def refactor_code(ctx: Context, code: str, instruction: str, model: str = "o4-mini") -> str:
    """Refactor *code* as per *instruction*."""
    logger.info("TOOL REQUEST: refactor_code - model=%s", model)

    prompt = (
        "# Task: Code Refactoring\n"
        "You are a software architect specializing in clean code and software design principles.\n\n"
        "## Original Code\n" + code.strip() + "\n\n" +
        "## Refactoring Goal\n" + instruction.strip() + "\n\n" +
        "## Refactoring Guidelines\n"
        "- Preserve all functionality and behavior\n"
        "- Improve code readability and maintainability\n"
        "- Apply established design patterns where appropriate\n"
        "- Follow language best practices and conventions\n"
        "- Maintain or improve performance where possible\n\n"
        "## Output Format\n"
        "Provide only the refactored code. Do not include explanations."
    )

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_tests(ctx: Context, code: str, description: str = "", model: str = "o4-mini") -> str:
    """Generate unit tests for *code*."""
    logger.info("TOOL REQUEST: write_tests - model=%s", model)

    prompt = (
        "# Task: Test Development\n"
        "You are a QA engineer with expertise in test-driven development.\n\n"
        "## Code Under Test\n" + code.strip() + "\n\n" +
        (f"## Additional Context\n{description}\n\n" if description else "") +
        "## Testing Requirements\n"
        "- Write comprehensive unit tests covering all major functionality\n"
        "- Include edge cases and error scenarios\n"
        "- Follow standard testing patterns and libraries for the language\n"
        "- Aim for high code coverage\n"
        "- Include setup/teardown as needed\n\n"
        "## Output Format\n"
        "Provide only the test code. Do not include explanations outside of necessary test documentation."
    )

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def explain_code(ctx: Context, code: str, detail_level: str = "medium", model: str = "o4-mini") -> str:
    """Explain the functionality and structure of the provided *code*.
    
    The *detail_level* can be 'brief', 'medium', or 'detailed'.
    """
    logger.info("TOOL REQUEST: explain_code - detail_level=%s, model=%s", detail_level, model)
    
    prompt = (
        "# Task: Code Explanation\n"
        f"You are a technical educator tasked with explaining code to {detail_level} level of detail.\n\n"
        "## Code to Explain\n" + code.strip() + "\n\n" +
        f"## Explanation Guidelines for '{detail_level}' Detail Level\n" +
        "- Brief: Provide a concise 2-3 sentence high-level overview of what the code does\n" +
        "- Medium: Explain main functions/classes and their purposes, key algorithms, and overall structure\n" +
        "- Detailed: Provide comprehensive breakdown of all components, logic flows, design patterns, and potential edge cases\n\n"
        "## Focus Areas\n" +
        "- Overall purpose and functionality\n" +
        "- Key algorithms and data structures\n" +
        "- Control flow and execution path\n" +
        "- Important design patterns or techniques used\n" +
        "- Potential performance considerations or limitations"
    )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def generate_docs(ctx: Context, code: str, doc_format: str = "docstring", model: str = "o4-mini") -> str:
    """Generate documentation for the provided *code*.
    
    The *doc_format* can be 'docstring', 'markdown', or 'html'.
    """
    logger.info("TOOL REQUEST: generate_docs - doc_format=%s, model=%s", doc_format, model)
    
    prompt = (
        "# Task: Documentation Generation\n"
        "You are a technical writer creating professional documentation for code.\n\n"
        "## Code to Document\n" + code.strip() + "\n\n" +
        f"## Documentation Format: {doc_format}\n" +
        "- docstring: Generate language-appropriate docstrings embedded in the code\n" +
        "- markdown: Create standalone markdown documentation with sections for classes, functions, usage examples\n" +
        "- html: Produce HTML documentation with proper structure, highlighting, and navigation\n\n" +
        "## Documentation Requirements\n" +
        "- Clearly describe all functions, classes, and methods\n" +
        "- Document parameters, return types, and exceptions\n" +
        "- Include usage examples for key components\n" +
        "- Specify any important dependencies or requirements\n" +
        "- Follow best practices for the specified documentation format\n\n" +
        "## Output Format\n" +
        "Provide only the documentation without any additional explanations."
    )
    
    return await _query_codex(ctx, prompt, model=model)
