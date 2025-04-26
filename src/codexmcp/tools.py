"""FastMCP tools exposed by *CodexMCP*."""

from __future__ import annotations

import json
import os
import tempfile
import importlib.resources  # Use importlib.resources
from typing import Any, Dict, List, Literal, Optional

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
async def assess_code_quality(ctx: Context, code: str, language: str = "Python", focus_areas: List[str] = [], model: str = DEFAULT_MODEL) -> str:
    """Assess code quality and provide improvement suggestions.
    
    Args:
        ctx: The FastMCP context.
        code: The code to assess.
        language: Programming language.
        focus_areas: Specific areas to focus on (e.g., "performance", "readability", "security").
        model: The OpenAI model to use.
    
    Returns:
        Code quality assessment with actionable improvement suggestions.
    """
    logger.info("TOOL REQUEST: assess_code_quality - language=%s, model=%s", language, model)
    
    template = _load_prompt("assess_code_quality")
    
    # Format focus areas for the prompt
    focus_areas_text = ""
    if focus_areas:
        focus_areas_text = "\n\n## Focus Areas\nPlease pay special attention to these aspects:\n"
        focus_areas_text += "\n".join([f"- {area}" for area in focus_areas])
    
    prompt = template.format(
        code=code.strip(),
        language=language,
        focus_areas=focus_areas_text
    )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def migrate_code(ctx: Context, code: str, from_version: str, to_version: str, language: str = "Python", model: str = DEFAULT_MODEL) -> str:
    """Migrate code between different language versions or frameworks.
    
    Args:
        ctx: The FastMCP context.
        code: The code to migrate.
        from_version: Source version/framework (e.g., "Python 2", "React 16").
        to_version: Target version/framework (e.g., "Python 3", "React 18").
        language: Base programming language.
        model: The OpenAI model to use.
    
    Returns:
        Migrated code with explanation of changes.
    """
    logger.info("TOOL REQUEST: migrate_code - from=%s, to=%s, model=%s", 
                from_version, to_version, model)
    
    template = _load_prompt("migrate_code")
    prompt = template.format(
        code=code.strip(),
        from_version=from_version,
        to_version=to_version,
        language=language
    )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def refactor_code(ctx: Context, code: str, instruction: str, model: str = DEFAULT_MODEL) -> str:
    """[DEPRECATED] Refactor *code* as per *instruction*.
    
    This tool is deprecated and will be removed in a future version.
    Please use `assess_code_quality` or `migrate_code` instead.
    """
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
async def write_tests(ctx: Context, code: str, description: str = "", model: str = DEFAULT_MODEL) -> str:
    """Generate unit tests for *code*."""
    logger.info("TOOL REQUEST: write_tests - model=%s", model)
    template = _load_prompt("write_tests")
    # Handle optional description formatting
    desc_section = f"\n\n## Additional Context\n{description}" if description else ""
    prompt = template.format(code=code.strip(), description=desc_section)
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def explain_code_for_audience(ctx: Context, code: str, audience: str = "developer", detail_level: str = "medium", model: str = DEFAULT_MODEL) -> str:
    """Explain code with customized detail level for different audiences.
    
    Args:
        ctx: The FastMCP context.
        code: The code to explain.
        audience: Target audience (e.g., "developer", "manager", "beginner").
        detail_level: Level of detail ("brief", "medium", "detailed").
        model: The OpenAI model to use.
    
    Returns:
        Code explanation tailored to the specified audience and detail level.
    """
    logger.info("TOOL REQUEST: explain_code_for_audience - audience=%s, detail_level=%s, model=%s", 
                audience, detail_level, model)
    
    template = _load_prompt("explain_code_for_audience")
    prompt = template.format(
        code=code.strip(),
        audience=audience,
        detail_level=detail_level
    )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def explain_code(ctx: Context, code: str, detail_level: str = "medium", model: str = DEFAULT_MODEL) -> str:
    """[DEPRECATED] Explain the functionality and structure of the provided *code*.
    
    This tool is deprecated and will be removed in a future version.
    Please use `explain_code_for_audience` instead.
    
    The *detail_level* can be 'brief', 'medium', or 'detailed'.
    """
    logger.warning("DEPRECATION WARNING: 'explain_code' is deprecated. Use 'explain_code_for_audience' instead.")
    
    # Call the new tool with appropriate defaults
    return await explain_code_for_audience(
        ctx, 
        code=code, 
        audience="developer",  # Default audience
        detail_level=detail_level,
        model=model
    )


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
async def analyze_code_context(ctx: Context, code: str, file_path: str = "", surrounding_files: List[str] = [], model: str = DEFAULT_MODEL) -> str:
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
    logger.info("TOOL REQUEST: analyze_code_context - model=%s", model)
    template = _load_prompt("analyze_code_context")
    
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
    prompt = template.format(
        code=code.strip(),
        file_path=file_path,
        context=context_text
    )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def interactive_code_generation(ctx: Context, description: str, language: str = "Python", feedback: str = "", iteration: int = 1, model: str = DEFAULT_MODEL) -> str:
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
    logger.info("TOOL REQUEST: interactive_code_generation - language=%s, iteration=%d, model=%s", 
                language, iteration, model)
    
    template = _load_prompt("interactive_code_generation")
    
    # Adjust prompt based on whether this is the first iteration or a refinement
    if iteration > 1 and feedback:
        prompt = template.format(
            description=description.strip(),
            language=language,
            feedback_section=f"\n\n## Previous Feedback\n{feedback.strip()}",
            iteration=iteration
        )
    else:
        prompt = template.format(
            description=description.strip(),
            language=language,
            feedback_section="",
            iteration=1
        )
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def generate_from_template(ctx: Context, template_name: str, parameters: Dict[str, str], language: str = "Python", model: str = DEFAULT_MODEL) -> str:
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
    logger.info("TOOL REQUEST: generate_from_template - template=%s, language=%s, model=%s", 
                template_name, language, model)
    
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
    
    return await _query_codex(ctx, prompt, model=model)


@mcp.tool()
async def search_codebase(ctx: Context, query: str, file_patterns: List[str] = ["*.py", "*.js", "*.ts"], max_results: int = 5, model: str = DEFAULT_MODEL) -> str:
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
    logger.info("TOOL REQUEST: search_codebase - query=%s, model=%s", query, model)
    
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
    
    template = _load_prompt("search_codebase")
    prompt = template.format(
        query=query,
        search_results="\n\n".join(search_results[:max_results])
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
