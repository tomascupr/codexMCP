"""FastMCP tools exposed by *CodexMCP*."""

from __future__ import annotations

import json
import os
import tempfile
import importlib.resources  # Use importlib.resources
from typing import Any, Dict, List, Literal, Optional
import asyncio # Add asyncio for subprocess
import shutil # Add shutil for which function

# ---------------------------------------------------------------------------
# Optional OpenAI SDK import (lazy fallback when Codex CLI absent)
# ---------------------------------------------------------------------------

try:
    # The official OpenAI Python client v1.x exposes AsyncOpenAI
    import openai  # type: ignore

    _OPENAI_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover – only executed when dependency missing
    _OPENAI_SDK_AVAILABLE = False

from fastmcp import Context, exceptions

# Local imports
from .config import config
from .exceptions import (
    CodexBaseError,
    CodexRateLimitError,
    CodexTimeoutError,
    CodexModelUnavailableError,
    CodexConnectionError,
)
from .logging_cfg import logger
from .shared import mcp  # Import MCP only; CodexPipe is no longer used
from .prompts import prompts
from .cli_backend import run as _cli_run


# Helper to load templates
def _load_template(name: str) -> str:
    try:
        # Assumes templates are in a 'templates' subdirectory relative to this file's package
        return importlib.resources.read_text(__package__ + '.templates', f"{name}.txt")
    except FileNotFoundError as exc:
        logger.error("Template file '%s.txt' not found in package '%s.templates'", name, __package__, exc_info=True)
        # Fallback to generic template
        try:
            return _load_prompt("generic_template")
        except Exception:
            raise exceptions.ToolError(f"Internal server error: Missing template '{name}' and generic fallback.") from exc
    except Exception as exc:
        logger.error("Failed to load template '%s': %s", name, exc, exc_info=True)
        raise exceptions.ToolError(f"Internal server error: Could not load template '{name}'.") from exc


# Keep original _load_prompt function for backward compatibility
def _load_prompt(name: str) -> str:
    """Legacy helper to load prompts."""
    try:
        return prompts.get(name)
    except ValueError as exc:
        logger.error("Prompt file '%s.txt' not found", name, exc_info=True)
        raise exceptions.ToolError(f"Internal server error: Missing prompt template '{name}'.") from exc
    except Exception as exc:
        logger.error("Failed to load prompt '%s': %s", name, exc, exc_info=True)
        raise exceptions.ToolError(f"Internal server error: Could not load prompt template '{name}'.") from exc


async def _query_codex(ctx: Context, prompt: str, *, model: str) -> str:
    """Send *prompt* to Codex CLI and return the completion.

    All FastMCP tools now delegate to Codex CLI exclusively so we keep this
    helper very thin: forward the call and adapt progress/error reporting.
    """

    # Optional user-visible progress
    if hasattr(ctx, "progress"):
        await ctx.progress("Generating with Codex CLI…")

    try:
        logger.info("Running Codex CLI with prompt: %s", prompt.replace('\n',' ')[:120])
        return await _cli_run(prompt, model)
    except Exception as exc:
        logger.error("Codex CLI failed: %s", exc, exc_info=True)
        # Preserve previous exception type hierarchy for callers
        raise CodexBaseError(str(exc), "cli_error") from exc


async def _query_codex_via_pipe(ctx: Context, prompt: str, *, model: str) -> str:
    """Query the Codex CLI by direct execution, processing a stream of JSON responses."""
    
    # This function now assumes direct execution of 'codex' with the prompt as an argument.
    # It will need access to the codex executable path and base arguments.
    # For this example, we'll try to reconstruct or assume access.
    # A more robust solution would involve shared.py exposing these.
    
    codex_exe = getattr(config, "codex_executable_path", shutil.which("codex")) # Attempt to get from config or find in PATH
    if not codex_exe:
        raise CodexBaseError("Codex executable path not configured or found.")

    # Base arguments for the codex CLI, excluding --pipe and dummy prompt
    # The prompt itself will be inserted after -q
    # Arguments like --json can usually precede -q
    pre_prompt_args = ["--json"]
    post_prompt_args = [
        "--approval-mode=full-auto",
        "--disable-shell"
        # model arg clarification still pending, see previous comments
    ]

    # Construct the command: codex_exe <pre_args> -q <prompt> <post_args>
    cmd = [codex_exe] + pre_prompt_args + ["-q", f'"{prompt}"'] + post_prompt_args
    logger.info("CLI cmd: %s", ' '.join(cmd))

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err_output = stderr.decode().strip() if stderr else "No stderr output"
        logger.error(f"Codex CLI failed with exit code {process.returncode}: {err_output}")
        raise CodexBaseError(f"Codex CLI execution failed: {err_output}")

    if not stdout:
        raise CodexBaseError("Codex CLI returned no output.")

    # Process the stream of JSON objects from stdout
    # Each JSON object is expected to be on a new line.
    lines = stdout.decode().strip().split('\n')
    final_completion = None

    for line_num, line_content in enumerate(lines):
        line_content = line_content.strip()
        if not line_content:
            continue
        
        # Skip JSON validation and parse directly
        response_obj = json.loads(line_content)
        logger.debug(f"Codex CLI JSON response line {line_num + 1}: {response_obj}")

        if response_obj.get("status") == "completed":
            # Found the completed response, extract content
            response_keys = ["completion", "text", "response", "content"]
            for key in response_keys:
                if key in response_obj:
                    if key == "content":
                        content_value = response_obj["content"]
                        if isinstance(content_value, list) and content_value and isinstance(content_value[0], dict) and "text" in content_value[0]:
                            final_completion = content_value[0]["text"].lstrip("\n")
                        else:
                            final_completion = str(content_value).lstrip("\n")
                    else:
                        final_completion = str(response_obj[key]).lstrip("\n")
                    logger.info(f"Codex CLI completed. Extracted from key '{key}'.")
                    break
            if final_completion is not None:
                break # Exit loop once completed content is found
            else:
                logger.warning("Codex CLI 'completed' status found, but no known content key ('completion', 'text', 'response').")
                # Continue in case there are multiple 'completed' messages or content is later

        elif "type" in response_obj: # Log other types of messages, e.g., reasoning
             logger.info(f"Codex CLI intermediate message: Type '{response_obj['type']}', Content: {response_obj}")
        
        # Potentially call progress_cb here with intermediate updates
        if hasattr(ctx, "progress") and callable(ctx.progress):
            # Determine what to send to progress, maybe the whole object or a summary
            await ctx.progress(f"CLI status: {response_obj.get('type', 'processing')}")

    if final_completion is not None:
        return final_completion
    else:
        logger.error("Codex CLI stream ended without a 'completed' status message containing usable content.")
        raise CodexBaseError("Codex CLI did not return a usable 'completed' response.")


@mcp.tool()
async def generate_code(ctx: Context, description: str, language: str = "Python", model: str | None = None) -> str:
    """Generate source code as described. Uses Codex CLI with full FS context."""
    model = model or config.default_model
    prompt = f"Generate {language} code that fulfils the following description:\n{description.strip()}"
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def assess_code_quality(
    ctx: Context,
    code: str | None = None,
    language: str = "Python",
    focus_areas: List[str] | None = None,
    extra_prompt: str | None = None,
    model: str | None = None,
) -> str:
    """Ask Codex to review code quality.

    If *code* is omitted the CLI can read the workspace; *extra_prompt* lets the
    caller provide free-form instructions (e.g. "especially security aspects").
    """

    model = model or config.default_model

    if code:
        if _is_probably_code(code):
            prompt = "Assess the quality of the following code:\n\n" + code.strip()
        else:
            # treat provided text as high-level instruction
            prompt = code.strip()
            code = None  # no inline code snippet
    else:
        prompt = "Assess the overall codebase quality."

    if focus_areas:
        prompt += "\n\nFocus on: " + ", ".join(focus_areas)

    if extra_prompt:
        prompt += "\n\n" + extra_prompt.strip()

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def migrate_code(
    ctx: Context,
    code: str | None = None,
    from_version: str = "",
    to_version: str = "",
    language: str = "Python",
    model: str | None = None,
) -> str:
    """Request Codex to migrate code or project between versions/frameworks."""

    model = model or config.default_model

    task_line = f"Migrate {language} code from {from_version or 'current version'} to {to_version or 'latest version'}."
    if code:
        prompt = task_line + "\n\nCode to migrate:\n" + code.strip()
    else:
        prompt = task_line + "\n\nApply changes across the repository as needed."

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_tests(ctx: Context, code: str | None = None, description: str = "", model: str | None = None) -> str:
    """Ask Codex to write unit tests."""
    model = model or config.default_model

    if code:
        prompt = "Write comprehensive unit tests for the following code:\n\n" + code.strip()
        if description:
            prompt += "\n\nAdditional context: " + description.strip()
    else:
        prompt = "Write comprehensive unit tests for the project." + (" " + description.strip() if description else "")

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def explain_code_for_audience(
    ctx: Context,
    code: str | None = None,
    audience: str = "developer",
    detail_level: str = "medium",
    model: str | None = None,
) -> str:
    """Explain code for a given audience/detail."""

    model = model or config.default_model
    levels = {"brief", "medium", "detailed"}
    if detail_level not in levels:
        detail_level = "medium"

    if code:
        if _is_probably_code(code):
            prompt = (
                f"Explain the following code to a {audience} in {detail_level} detail:\n\n" + code.strip()
            )
        else:
            prompt = f"{code.strip()}\n\n(Provide the explanation above to a {audience} in {detail_level} detail.)"
    else:
        prompt = f"Explain the project architecture to a {audience} in {detail_level} detail."

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def generate_docs(ctx: Context, code: str | None = None, doc_format: str = "docstring", model: str | None = None) -> str:
    """Ask Codex to generate documentation."""

    model = model or config.default_model
    formats = {"docstring", "markdown", "html"}
    if doc_format not in formats:
        doc_format = "docstring"

    if code:
        prompt = f"Generate {doc_format} documentation for the following code:\n\n" + code.strip()
    else:
        prompt = f"Generate {doc_format} documentation for the project."

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def refactor_code(ctx: Context, code: str, instruction: str, model: str = None) -> str:
    """[DEPRECATED] Refactor *code* as per *instruction*.
    
    This tool is deprecated and will be removed in a future version.
    Please use `assess_code_quality` or `migrate_code` instead.
    """
    model = model or config.default_model
    logger.warning("DEPRECATION WARNING: 'refactor_code' is deprecated. Use 'assess_code_quality' or 'migrate_code' instead.")
    
    # Determine which new tool to use based on the instruction
    if any(keyword in instruction.lower() for keyword in ["migrate", "convert", "upgrade", "version"]):
        # Default values for migration
        from_version = "current version"
        to_version = "latest version"
        language = "Python"
        
        # Try to extract language and versions from instruction
        instruction_lower = instruction.lower()
        
        # Simple language detection
        for lang in ["python", "javascript", "typescript", "java", "c#", "ruby", "go"]:
            if lang in instruction_lower:
                language = lang.capitalize()
                break
        
        # Simple version extraction (very basic)
        if "from" in instruction_lower and "to" in instruction_lower:
            parts = instruction_lower.split("from")
            if len(parts) > 1:
                from_parts = parts[1].split("to")
                if len(from_parts) > 1:
                    from_version = from_parts[0].strip()
                    to_parts = from_parts[1].split()
                    if to_parts:
                        to_version = to_parts[0].strip()
        
        return await migrate_code(
            ctx,
            code=code,
            from_version=from_version,
            to_version=to_version,
            language=language,
            model=model
        )
    else:
        # Default to code quality assessment
        return await assess_code_quality(
            ctx,
            code=code,
            language="Python",  # Default language
            focus_areas=[instruction],  # Use the instruction as a focus area
            model=model
        )


@mcp.tool()
async def explain_code(ctx: Context, *args, audience: str = "developer", detail_level: str = "medium", model: str | None = None) -> str:
    """High-level explanation of the current project or a specific snippet.

    examples:
        explain(ctx)                       # overview of repo
        explain(ctx, "README.md")        # explain that file
        explain(ctx, code_snippet)        # explain snippet
    """

    subject: str | None = args[0] if args else None  # first positional arg if provided
    model = model or config.default_model

    # Prefer first positional arg; otherwise capture the raw user utterance.
    if not subject:
        subject = getattr(ctx, "original_input", "").strip()

    # If we still have nothing meaningful, fall back to a very short request.
    prompt = subject or "Describe the current repository at a high level."

    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def write_openai_agent(ctx: Context, name: str, instructions: str, tool_functions: List[str] = [], description: str = "", model: str = None) -> str:
    """Generate Python code for an OpenAI Agent using the `openai-agents` SDK.

    Args:
        ctx: The FastMCP context.
        name: The desired name for the agent.
        instructions: The system prompt/instructions for the agent.
        tool_functions: A list of natural language descriptions for tools the agent should have.
        description: Optional additional details about the agent's behavior or tool implementation.
        model: The OpenAI model to use (e.g., 'o4-mini', 'gpt-4').
    """
    model = model or config.default_model
    logger.info("TOOL REQUEST: write_openai_agent - name=%s, model=%s", name, model)
    
    try:
        # Format the tool functions list for the prompt
        formatted_tool_funcs = "\n".join([f"- {func_desc}" for func_desc in tool_functions])
        if not formatted_tool_funcs:
            formatted_tool_funcs = "# No tools specified."
        
        # Get formatted prompt using prompt manager
        prompt = prompts.get(
            "write_openai_agent",
            name=name,
            instructions=instructions.strip(),
            tool_functions=formatted_tool_funcs,
            description=description.strip()
        )
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to generate agent code: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Agent code generation failed: {str(e)}")


@mcp.tool()
async def analyze_code_context(ctx: Context, code: str, file_path: str = "", surrounding_files: List[str] = [], model: str = None) -> str:
    """Analyze code with awareness of its surrounding context.
    
    Args:
        ctx: The FastMCP context.
        code: The code to analyze.
        file_path: Path to the file containing the code (for context).
        surrounding_files: List of related file paths to consider for context.
        model: The OpenAI model to use.
    
    Returns:
        Analysis with context-aware insights and suggestions.
    """
    model = model or config.default_model
    logger.info("TOOL REQUEST: analyze_code_context - model=%s", model)
    
    try:
        # Gather context from surrounding files if provided
        context_snippets = []
        if surrounding_files:
            context_snippets.append("## Related Files Context")
            for file in surrounding_files[:3]:  # Limit to 3 files to avoid token limits
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        # Include just enough context (first 50 lines or so)
                        content_preview = "\n".join(content.split("\n")[:50])
                        context_snippets.append(f"### {file}\n```\n{content_preview}\n```")
                except Exception as e:
                    context_snippets.append(f"### {file}\nError reading file: {str(e)}")
        
        context_text = "\n\n".join(context_snippets)
        
        # Get formatted prompt using prompt manager
        prompt = prompts.get(
            "analyze_code_context",
            code=code.strip(),
            file_path=file_path,
            context=context_text
        )
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to analyze code context: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Code context analysis failed: {str(e)}")


@mcp.tool()
async def interactive_code_generation(ctx: Context, description: str, language: str = "Python", feedback: str = "", iteration: int = 1, model: str = None) -> str:
    """Generate code with an iterative feedback loop.
    
    Args:
        ctx: The FastMCP context.
        description: Task description.
        language: Programming language.
        feedback: Feedback on previous iterations.
        iteration: Current iteration number.
        model: The OpenAI model to use.
    
    Returns:
        Generated code with explanation of changes based on feedback.
    """
    model = model or config.default_model
    logger.info("TOOL REQUEST: interactive_code_generation - language=%s, iteration=%d, model=%s", 
               language, iteration, model)
    
    try:
        # Adjust prompt based on whether this is the first iteration or a refinement
        feedback_section = ""
        if iteration > 1 and feedback:
            feedback_section = f"\n\n## Previous Feedback\n{feedback.strip()}"
        
        # Get formatted prompt using prompt manager
        prompt = prompts.get(
            "interactive_code_generation",
            description=description.strip(),
            language=language,
            feedback_section=feedback_section,
            iteration=iteration or 1
        )
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to generate code interactively: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Interactive code generation failed: {str(e)}")


@mcp.tool()
async def generate_from_template(ctx: Context, template_name: str, parameters: Dict[str, str], language: str = "Python", model: str = None) -> str:
    """Generate code using customizable templates.
    
    Args:
        ctx: The FastMCP context.
        template_name: Name of the template to use.
        parameters: Dictionary of parameters to fill in the template.
        language: Programming language.
        model: The OpenAI model to use.
    
    Returns:
        Generated code based on the template and parameters.
    """
    model = model or config.default_model
    logger.info("TOOL REQUEST: generate_from_template - template=%s, language=%s, model=%s", 
               template_name, language, model)
    
    try:
        # Load the template - this could be from a templates directory
        try:
            template_content = _load_template(template_name)
        except Exception as e:
            logger.warning("Failed to load template '%s': %s. Using generic template.", template_name, e)
            template_content = _load_prompt("generic_template")
        
        # Format the template with parameters
        formatted_template = template_content
        
        # Format parameters for the prompt if using generic template
        parameters_formatted = "\n".join([f"- {key}: {value}" for key, value in parameters.items()])
        
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            formatted_template = formatted_template.replace(placeholder, value)
        
        # Add language information
        prompt = f"# Template: {template_name}\n# Language: {language}\n\n{formatted_template}"
        
        # If using generic template, add parameters section
        if template_content == _load_prompt("generic_template"):
            prompt = prompt.replace("{parameters_formatted}", parameters_formatted)
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to generate from template: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Template code generation failed: {str(e)}")


@mcp.tool()
async def search_codebase(ctx: Context, query: str, file_patterns: List[str] = ["*.py", "*.js", "*.ts"], max_results: int = 5, model: str = None) -> str:
    """Search and analyze code across multiple files based on natural language query.
    
    Args:
        ctx: The FastMCP context.
        query: Natural language search query.
        file_patterns: File patterns to include in search.
        max_results: Maximum number of results to return.
        model: The OpenAI model to use.
    
    Returns:
        Search results with relevant code snippets and explanations.
    """
    model = model or config.default_model
    logger.info("TOOL REQUEST: search_codebase - query=%s, model=%s", query, model)
    
    try:
        # This would be implemented to use shell commands to search the codebase
        search_results = []
        
        # For each file pattern, run grep to find matches
        for pattern in file_patterns:
            try:
                # Create a temporary file for the grep command
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    f.write(f"find . -type f -name '{pattern}' -not -path '*/\\.*' | xargs grep -l '{query}' 2>/dev/null || true")
                    grep_script = f.name
                
                # Make the script executable
                os.chmod(grep_script, 0o755)
                
                # Execute the grep command
                import subprocess
                result = subprocess.run([grep_script], capture_output=True, text=True, shell=True)
                files_found = result.stdout.strip().split('\n')
                
                # Clean up
                os.unlink(grep_script)
                
                # Process the results
                for file in [f for f in files_found if f]:
                    try:
                        with open(file, 'r') as f:
                            content = f.read()
                            # Find relevant snippets based on query
                            lines = content.split('\n')
                            total_lines = len(lines)
                            
                            # Look for lines containing the query
                            matching_lines = []
                            for i, line in enumerate(lines):
                                if query.lower() in line.lower():
                                    # Get context (5 lines before and after)
                                    start = max(0, i - 5)
                                    end = min(total_lines, i + 6)
                                    matching_lines.append((start, end))
                            
                            # Merge overlapping ranges
                            if matching_lines:
                                merged_ranges = []
                                current_start, current_end = matching_lines[0]
                                
                                for start, end in matching_lines[1:]:
                                    if start <= current_end:
                                        current_end = max(current_end, end)
                                    else:
                                        merged_ranges.append((current_start, current_end))
                                        current_start, current_end = start, end
                                
                                merged_ranges.append((current_start, current_end))
                                
                                # Extract snippets from merged ranges
                                snippets = []
                                for start, end in merged_ranges[:3]:  # Limit to 3 snippets per file
                                    snippet = "\n".join(lines[start:end])
                                    snippets.append(f"Lines {start+1}-{end}:\n```\n{snippet}\n```")
                                
                                search_results.append(f"## {file}\n{' '.join(snippets)}")
                    except Exception as e:
                        search_results.append(f"Error reading {file}: {str(e)}")
            except Exception as e:
                search_results.append(f"Error searching {pattern}: {str(e)}")
        
        if not search_results:
            search_results = ["No matching files found."]
        
        # Get formatted prompt using prompt manager
        prompt = prompts.get(
            "search_codebase",
            query=query,
            search_results="\n\n".join(search_results[:max_results])
        )
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to search codebase: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"Codebase search failed: {str(e)}")


@mcp.tool()
async def generate_api_docs(
    ctx: Context, 
    code: str, 
    framework: str = "FastAPI",
    output_format: Literal["openapi", "swagger", "markdown", "code"] = "openapi",
    client_language: str = "Python",
    model: str = None
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
    model = model or config.default_model
    logger.info("TOOL REQUEST: generate_api_docs - framework=%s, output_format=%s, model=%s", 
               framework, output_format, model)
    
    try:
        # Validate output_format
        valid_formats = ["openapi", "swagger", "markdown", "code"]
        if output_format not in valid_formats:
            output_format = "openapi"  # Default if invalid
            logger.warning(f"Invalid output_format '{output_format}', defaulting to 'openapi'")
        
        # Get formatted prompt using prompt manager
        prompt = prompts.get(
            "generate_api_docs",
            code=code.strip(),
            framework=framework,
            output_format=output_format,
            client_language=client_language
        )
        
        # Pass to enhanced query function
        return await _query_codex(ctx, prompt, model=model)
    except Exception as e:
        logger.error(f"Failed to generate API docs: {str(e)}", exc_info=True)
        if isinstance(e, CodexBaseError):
            raise  # Pass through our custom errors
        raise exceptions.ToolError(f"API documentation generation failed: {str(e)}")

# Helper to build a very simple prompt from arbitrary keyword arguments
def _simple_prompt(tool_name: str, **kwargs) -> str:
    """Serialize *kwargs* into a minimal prompt for Codex CLI.

    The idea is to avoid rigid templates – we just list each argument so the
    model can infer intent.  Empty / None values are skipped.
    """
    lines = [tool_name.replace("_", " ").title() + ":"]
    for key, value in kwargs.items():
        if key == "ctx" or key == "model":
            continue
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (list, dict)):
            import json as _json
            val_str = _json.dumps(value, indent=2)
        else:
            val_str = str(value)
        lines.append(f"{key}:\n{val_str}")
    return "\n\n".join(lines)

def _is_probably_code(text: str) -> bool:
    """Heuristic to guess whether *text* is source code or plain language."""
    code_indicators = ["def ", "class ", "import ", "{", ";", "=>", "<html", "function "]
    return any(tok in text for tok in code_indicators) or "\n" in text and len(text.split()) > 10

# ---------------------------------------------------------------------------
# Aliases / simplified public tool set
# ---------------------------------------------------------------------------

# 1. assess_code – umbrella for quality / migration / other assessments
@mcp.tool()
async def assess_code(ctx: Context, *args, **kwargs):  # type: ignore[valid-type]
    """Alias to `assess_code_quality` for the contracted public API."""
    return await assess_code_quality(ctx, *args, **kwargs)  # type: ignore[arg-type]


# 2. explain – high-level explanation helper
@mcp.tool()
async def explain(
    ctx: Context,
    *args,
    audience: str = "developer",
    detail_level: str = "medium",
    model: str | None = None,
):
    """High-level explanation of the current project or a specific snippet.

    examples:
        explain(ctx)                       # overview of repo
        explain(ctx, "README.md")        # explain that file
        explain(ctx, code_snippet)        # explain snippet
    """

    subject: str | None = args[0] if args else None  # first positional arg if provided
    model = model or config.default_model

    # Prefer first positional arg; otherwise capture the raw user utterance.
    if not subject:
        subject = getattr(ctx, "original_input", "").strip()

    # If we still have nothing meaningful, fall back to a very short request.
    prompt = subject or "Describe the current repository at a high level."

    return await _query_codex(ctx, prompt, model=model)