"""FastMCP tools exposed by *CodexMCP*."""

from __future__ import annotations

import json
import importlib.resources  # Use importlib.resources
from typing import Any, List, Literal

from fastmcp import Context, exceptions

from .logging_cfg import logger
from .shared import mcp, pipe, DEFAULT_MODEL  # Import DEFAULT_MODEL


# Helper to load prompts
def _load_prompt(name: str) -> str:
    try:
        # Assumes prompts are in a 'prompts' subdirectory relative to this file's package
        return importlib.resources.read_text(__package__ + '.prompts', f"{name}.txt")
    except FileNotFoundError as exc:
        logger.error("Prompt file '%s.txt' not found in package '%s.prompts'", name, __package__, exc_info=True)
        # Fallback or raise a more specific error
        raise exceptions.ToolError(f"Internal server error: Missing prompt template '{name}'.") from exc
    except Exception as exc:
        logger.error("Failed to load prompt '%s': %s", name, exc, exc_info=True)
        raise exceptions.ToolError(f"Internal server error: Could not load prompt template '{name}'.") from exc


async def _query_codex(ctx: Context, prompt: str, *, model: str) -> str: # model is now required here
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
async def generate_code(ctx: Context, description: str, language: str = "Python", model: str = DEFAULT_MODEL) -> str:
    """Generate *language* source code that fulfils *description*."""
    logger.info("TOOL REQUEST: generate_code - language=%s, model=%s", language, model)
    template = _load_prompt("generate_code")
    prompt = template.format(language=language, description=description)
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def refactor_code(ctx: Context, code: str, instruction: str, model: str = DEFAULT_MODEL) -> str:
    """Refactor *code* as per *instruction*."""
    logger.info("TOOL REQUEST: refactor_code - model=%s", model)
    template = _load_prompt("refactor_code")
    # Use strip() on inputs before formatting
    prompt = template.format(code=code.strip(), instruction=instruction.strip())
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_tests(ctx: Context, code: str, description: str = "", model: str = DEFAULT_MODEL) -> str:
    """Generate unit tests for *code*."""
    logger.info("TOOL REQUEST: write_tests - model=%s", model)
    template = _load_prompt("write_tests")
    # Handle optional description formatting
    desc_section = f"\n\n## Additional Context\n{description}" if description else ""
    prompt = template.format(code=code.strip(), description=desc_section)
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def explain_code(ctx: Context, code: str, detail_level: str = "medium", model: str = DEFAULT_MODEL) -> str:
    """Explain the functionality and structure of the provided *code*.
    
    The *detail_level* can be 'brief', 'medium', or 'detailed'.
    """
    logger.info("TOOL REQUEST: explain_code - detail_level=%s, model=%s", detail_level, model)
    template = _load_prompt("explain_code")
    prompt = template.format(code=code.strip(), detail_level=detail_level)
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def generate_docs(ctx: Context, code: str, doc_format: str = "docstring", model: str = DEFAULT_MODEL) -> str:
    """Generate documentation for the provided *code*.
    
    The *doc_format* can be 'docstring', 'markdown', or 'html'.
    """
    logger.info("TOOL REQUEST: generate_docs - doc_format=%s, model=%s", doc_format, model)
    template = _load_prompt("generate_docs")
    prompt = template.format(code=code.strip(), doc_format=doc_format)
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_openai_agent(ctx: Context, name: str, instructions: str, tool_functions: List[str] = [], description: str = "", model: str = DEFAULT_MODEL) -> str:
    """Generate Python code for an OpenAI Agent using the `openai-agents` SDK.

    Args:
        ctx: The FastMCP context.
        name: The desired name for the agent.
        instructions: The system prompt/instructions for the agent.
        tool_functions: A list of natural language descriptions for tools the agent should have.
        description: Optional additional details about the agent's behavior or tool implementation.
        model: The OpenAI model to use (e.g., 'o4-mini', 'gpt-4').
    """
    logger.info("TOOL REQUEST: write_openai_agent - name=%s, model=%s", name, model)
    template = _load_prompt("write_openai_agent")

    # Format the tool functions list for the prompt
    formatted_tool_funcs = "\n".join([f"- {func_desc}" for func_desc in tool_functions])
    if not formatted_tool_funcs:
        formatted_tool_funcs = "# No tools specified."

    prompt = template.format(
        name=name,
        instructions=instructions.strip(),
        tool_functions=formatted_tool_funcs,
        description=description.strip()
    )
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def generate_api_docs(
    ctx: Context, 
    code: str, 
    framework: str = "FastAPI",
    output_format: Literal["openapi", "swagger", "markdown", "code"] = "openapi",
    client_language: str = "Python",
    model: str = DEFAULT_MODEL
) -> str:
    """Generate API documentation or client code from API implementation code.
    
    Args:
        ctx: The FastMCP context.
        code: The API implementation code to document.
        framework: The web framework used (e.g., 'FastAPI', 'Flask', 'Express').
        output_format: The desired documentation format ('openapi', 'swagger', 'markdown', or 'code').
        client_language: The language for client code generation (when output_format is 'code').
        model: The OpenAI model to use.
    
    Returns:
        Generated API documentation or client code based on the specified format.
    """
    logger.info("TOOL REQUEST: generate_api_docs - framework=%s, output_format=%s, model=%s", 
                framework, output_format, model)
    
    template = _load_prompt("generate_api_docs")
    
    prompt = template.format(
        code=code.strip(),
        framework=framework,
        output_format=output_format,
        client_language=client_language
    )
    
    return await _query_codex(ctx, prompt, model=model)
