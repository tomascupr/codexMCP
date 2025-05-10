"""FastMCP tools exposed by *CodexMCP*."""

from __future__ import annotations

import os
import importlib.resources  # Use importlib.resources
from typing import Dict, List

# ---------------------------------------------------------------------------
# Optional OpenAI SDK import (lazy fallback when Codex CLI absent)
# ---------------------------------------------------------------------------

try:
    # Check for OpenAI SDK availability without importing unused module
    import importlib.util

    _OPENAI_SDK_AVAILABLE = importlib.util.find_spec("openai") is not None
except ImportError:  # pragma: no cover – only executed when dependency missing
    _OPENAI_SDK_AVAILABLE = False

from fastmcp import Context, exceptions

# Local imports
from .config import config
from .exceptions import (
    CodexBaseError,
)
from .logging_cfg import logger
from .shared import mcp, client  # Import MCP and shared client for OpenAI streaming
from .prompts import prompts
from .cli_backend import run as _cli_run


# Helper to load templates
def _load_template(name: str) -> str:
    try:
        # Assumes templates are in a 'templates' subdirectory relative to this file's package
        return importlib.resources.read_text(__package__ + ".templates", f"{name}.txt")
    except FileNotFoundError as exc:
        logger.error(
            "Template file '%s.txt' not found in package '%s.templates'",
            name,
            __package__,
            exc_info=True,
        )
        # Fallback to generic template
        try:
            return _load_prompt("generic_template")
        except Exception:
            raise exceptions.ToolError(
                f"Internal server error: Missing template '{name}' and generic fallback."
            ) from exc
    except Exception as exc:
        logger.error("Failed to load template '%s': %s", name, exc, exc_info=True)
        raise exceptions.ToolError(
            f"Internal server error: Could not load template '{name}'."
        ) from exc


# Keep original _load_prompt function for backward compatibility
def _load_prompt(name: str) -> str:
    """Legacy helper to load prompts."""
    try:
        return prompts.get(name)
    except ValueError as exc:
        logger.error("Prompt file '%s.txt' not found", name, exc_info=True)
        raise exceptions.ToolError(
            f"Internal server error: Missing prompt template '{name}'."
        ) from exc
    except Exception as exc:
        logger.error("Failed to load prompt '%s': %s", name, exc, exc_info=True)
        raise exceptions.ToolError(
            f"Internal server error: Could not load prompt template '{name}'."
        ) from exc


async def _query_openai_stream(ctx: Context, prompt: str, *, model: str) -> str:
    """Send prompt to OpenAI API with streaming and return the completed text.

    This is only used as a fallback when Codex CLI is not available.
    """
    if hasattr(ctx, "progress") and callable(ctx.progress):
        await ctx.progress("Using OpenAI API...")

    content = ""
    api_params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.default_temperature,
        "max_tokens": config.default_max_tokens,
        "stream": True,
    }

    try:
        # Get streaming response from OpenAI
        stream = client.client.chat.completions.create(**api_params)

        # Process each chunk as it arrives
        async for chunk in stream:
            delta = getattr(chunk.choices[0], "delta", None)
            token = ""

            if delta and hasattr(delta, "content"):
                token = delta.content or ""
            elif hasattr(chunk.choices[0].message, "content"):
                token = chunk.choices[0].message.content or ""

            if token:
                content += token
                # Both report progress to context and print to console
                if hasattr(ctx, "progress") and callable(ctx.progress):
                    await ctx.progress(token)
                # Also print directly to console for real-time feedback
                print(token, end="", flush=True)

        return content
    except Exception as e:
        logger.error("OpenAI API error: %s", str(e), exc_info=True)
        # Try non-streaming as last resort
        return await client.generate(prompt, model=model)


async def _query_codex(ctx: Context, prompt: str, *, model: str) -> str:
    """Send *prompt* to Codex CLI and return the completion.

    This is the core function that all tools use to query the language model.
    It prioritizes using the Codex CLI and falls back to the OpenAI API if needed.
    """
    # Show progress to user if context supports it
    if hasattr(ctx, "progress") and callable(ctx.progress):
        await ctx.progress("Generating response...")

    try:
        # Direct call to CLI backend
        return await _cli_run(prompt, model)
    except Exception as exc:
        # Fall back to OpenAI API if Codex CLI fails and we have API access
        if _OPENAI_SDK_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            logger.warning(
                "Codex CLI failed (%s). Falling back to OpenAI API.", type(exc).__name__
            )
            return await _query_openai_stream(ctx, prompt, model=model)

        # No fallback available - propagate the error
        logger.error("Generation failed: %s", exc, exc_info=True)
        error_msg = f"Failed to generate response: {str(exc)}"
        raise CodexBaseError(error_msg, "generation_error") from exc


@mcp.tool()
async def code_generate(
    ctx: Context,
    description: str,
    language: str = "Python",
    template_name: str = "",
    parameters: Dict[str, str] | None = None,
    feedback: str = "",
    iteration: int = 1,
    model: str | None = None,
) -> str:
    """Generate code based on a description, template, or feedback.

    Args:
        ctx: The FastMCP context.
        description: What code to generate.
        language: Programming language to use.
        template_name: Optional template name to use.
        parameters: Parameters for the template.
        feedback: Feedback on previous iterations.
        iteration: Current iteration number.
        model: The LLM model to use.

    Returns:
        Generated code with explanations.
    """
    model_to_use = model or config.default_model
    parameters = parameters or {}

    try:
        # Construct the prompt based on the provided parameters
        if template_name:
            logger.info(
                "TOOL REQUEST: code_generate with template - template=%s, language=%s",
                template_name,
                language,
            )

            # Load the template
            try:
                template_content = _load_template(template_name)
            except Exception as e:
                logger.warning(
                    "Failed to load template '%s': %s. Using generic template.",
                    template_name,
                    e,
                )
                template_content = _load_prompt("generic_template")

            # Format the template with parameters
            formatted_template = template_content
            for key, value in parameters.items():
                placeholder = f"{{{key}}}"
                formatted_template = formatted_template.replace(placeholder, value)

            # Build the prompt with template
            prompt = f"# Template: {template_name}\n# Language: {language}\n\n{formatted_template}"

        elif feedback or iteration > 1:
            logger.info(
                "TOOL REQUEST: code_generate with feedback - language=%s, iteration=%d",
                language,
                iteration,
            )

            # Adjust prompt based on whether this is the first iteration or a refinement
            feedback_section = ""
            if iteration > 1 and feedback:
                feedback_section = f"\n\n## Previous Feedback\n{feedback.strip()}"

            # Get formatted prompt for interactive generation
            prompt = prompts.get(
                "interactive_code_generation",
                description=description.strip(),
                language=language,
                feedback_section=feedback_section,
                iteration=iteration or 1,
            )

        else:
            # Basic code generation
            logger.info("TOOL REQUEST: code_generate - language=%s", language)
            prompt = f"Generate {language} code that fulfils the following description:\n{description.strip()}"

        # Execute the prompt with Codex
        return await _query_codex(ctx, prompt, model=model_to_use)
    except Exception as e:
        logger.error(f"Failed in code_generate: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Code generation failed: {str(e)}")


@mcp.tool()
async def describe_codebase(
    ctx: Context,
    subject: str | None = None,
    audience: str = "developer",
    detail_level: str = "medium",  # brief, medium, detailed
    model: str | None = None,
) -> str:
    """Explain the repository, a file, or a code snippet."""
    model_to_use = model or config.default_model
    logger.info(
        "TOOL REQUEST: describe_codebase - subject=%s, detail_level=%s",
        subject or "repository",
        detail_level,
    )

    try:
        prompt_text = ""
        if subject:
            # Basic check if it might be a file path that exists
            if os.path.isfile(subject):  # Checks if it's an existing regular file
                try:
                    with open(subject, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    # Limit context sent to LLM for very large files
                    prompt_text = f"Explain the following code from file '{subject}' to a {audience} in {detail_level} detail (be concise if the code is long):\n\n{file_content[:3000]}"
                except Exception as e:
                    logger.warning(
                        f"Could not read file {subject} for describe_codebase: {e}"
                    )
                    # Fallback to treating subject as a general query/snippet
                    prompt_text = f"Explain the following code, concept, or file path '{subject}' to a {audience} in {detail_level} detail."
            else:  # Assume it's a code snippet or question if not an existing file
                prompt_text = f"Explain the following code or concept '{subject}' to a {audience} in {detail_level} detail."
        else:
            prompt_text = f"Describe the current repository's architecture to a {audience} in {detail_level} detail."

        return await _query_codex(ctx, prompt_text, model=model_to_use)
    except Exception as e:
        logger.error(f"Failed in describe_codebase: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Code description failed: {str(e)}")


@mcp.tool()
async def review_code(
    ctx: Context,
    code: str | None = None,
    language: str = "Python",
    focus_areas: List[str] | None = None,
    extra_prompt: str | None = None,
    model: str | None = None,
) -> str:
    """Assess code quality, security, style or other aspects."""
    model_to_use = model or config.default_model
    logger.info("TOOL REQUEST: review_code - language=%s", language)

    try:
        if code:
            if _is_probably_code(code):
                prompt = "Assess the quality of the following code:\n\n" + code.strip()
            else:
                # treat provided text as high-level instruction
                prompt = code.strip()
        else:
            prompt = "Assess the overall codebase quality."

        if focus_areas:
            prompt += "\n\nFocus on: " + ", ".join(focus_areas)

        if extra_prompt:
            prompt += "\n\n" + extra_prompt.strip()

        return await _query_codex(ctx, prompt, model=model_to_use)
    except Exception as e:
        logger.error(f"Failed in review_code: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Code review failed: {str(e)}")


def _is_probably_code(text: str) -> bool:
    """Check if *text* is likely code (vs natural language query).

    Heuristic: if more than 1/3 of lines contain common code-like characters
    or keywords, and it's not excessively long (to avoid huge pastes).
    """
    code_indicators = [
        "def ",
        "class ",
        "import ",
        "{",
        ";",
        "=>",
        "<html",
        "function ",
    ]
    lines = text.split("\n")
    code_lines = [line for line in lines if any(tok in line for tok in code_indicators)]
    return len(code_lines) > len(lines) / 3 and len(text) < 1000
