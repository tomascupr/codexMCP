# CodexMCP

[![PyPI version](https://badge.fury.io/py/codexmcp.svg)](https://badge.fury.io/py/codexmcp)
[![GitHub release](https://img.shields.io/github/v/release/tomascupr/codexMCP)](https://github.com/tomascupr/codexMCP/releases)

Current version: **0.1.5**

## What is CodexMCP?

CodexMCP is a service that gives your applications access to AI coding capabilities without needing to build complex integrations. It's a server that exposes powerful code-related AI tools through a simple, standardized API.

**Important:** CodexMCP is **not** an autonomous agent - it's a tool provider that responds to specific requests. Your application remains in control, making specific requests for code generation, refactoring, or documentation as needed.

Think of CodexMCP as a bridge between your application and OpenAI's powerful AI coding capabilities. You send structured requests to the server (like "generate Python code that sorts a list"), and it returns the requested code or documentation.

A minimal FastMCP server wrapping the [OpenAI Codex CLI](https://github.com/openai/codex) to provide AI code generation, refactoring, and documentation capabilities through a standardized API.

## New Features

CodexMCP has been enhanced with several key improvements:

### 1. Streamlined Codex CLI Integration

The latest update removes the long-lived CodexPipe in favor of per-call CLI execution, improving reliability and simplifying the architecture. All tools now route through a new dedicated `cli_backend` module.

### 2. Simplified Tool Structure

The tools API has been reorganized for clarity and ease of use, with a focus on the most essential coding tasks:
- `generate_code`: Create new code across languages
- `assess_code`: Evaluate and improve existing code
- `explain`: Provide context-aware explanations 
- `search_codebase`: Find relevant code sections
- `write_tests`: Generate comprehensive test suites
- `write_openai_agent`: Create OpenAI agent implementations

### 3. Context-Aware Code Analysis

The new `analyze_code_context` tool allows you to analyze code with awareness of its surrounding context, including related files. This provides deeper insights into how code fits into the broader architecture.

### 4. Interactive Code Generation with Feedback Loop

The `interactive_code_generation` tool enables an iterative approach to code generation, where you can provide feedback on previous iterations to refine the results.

### 5. Advanced Code Quality Assessment

The `assess_code_quality` tool provides detailed code quality assessments with actionable suggestions for improvement, focusing on specific areas like performance, readability, or security.

### 6. Intelligent Code Search

The `search_codebase` tool allows you to search and analyze code across multiple files using natural language queries, making it easier to navigate large codebases.

### 7. Audience-Targeted Code Explanations

The `explain_code_for_audience` tool provides code explanations tailored to different audiences (developers, managers, beginners) with customizable detail levels.

### 8. Code Migration and Modernization

The `migrate_code` tool helps you migrate code between different language versions or frameworks, with explanations of the changes made.

### 9. Template-Based Code Generation

The `generate_from_template` tool enables code generation using customizable templates, increasing productivity for common tasks.

## Installation

1. **Prerequisites**:
   - Node.js 18 LTS or later
   - Python 3.10 or later
   - [Codex CLI](https://github.com/openai/codex) installed globally:

     ```bash
     npm install -g @openai/codex
     ```
     
     **Note**: If you don't have access to the Codex CLI, you can still use 
     CodexMCP with the OpenAI API fallback (see Python-only fallback below).

2. **Install CodexMCP**:

   ```bash
   pip install codexmcp
   ```

   **Optional (test dependencies)**:

   ```bash
   pip install codexmcp[test]
   ```

3. **(Optional) Python-only fallback**

   If you *don't* want to install the Node-based Codex CLI you can instead
   install the OpenAI Python SDK extra:

   ```bash
   # installs codexmcp + openai
   pip install "codexmcp[openai]"
   ```

   Make sure `OPENAI_API_KEY` is set in your environment or `.env` file.  At
   runtime CodexMCP will automatically fall back to the OpenAI ChatCompletion
   API whenever the `codex` executable cannot be found.

4. **Environment Setup**:
   - Create a `.env` file in your project root.
   - Add your OpenAI API key:

     ```ini
     OPENAI_API_KEY=sk-your-key-here
     ```
   - Optional environment variables:
     - `CODEXMCP_DEFAULT_MODEL`: Default model to use (default: "o4-mini").
     - `CODEXMCP_LOG_LEVEL`: Logging level (default: INFO).
     - `CODEXMCP_CONSOLE_LOG`: Enable console logging (default: true).
     - `CODEXMCP_CACHE_ENABLED`: Enable response caching (default: true).
     - `CODEXMCP_CACHE_TTL`: Cache time-to-live in seconds (default: 3600).
     - `CODEXMCP_MAX_RETRIES`: Maximum retry attempts for API calls (default: 3).
     - `CODEXMCP_RETRY_BACKOFF`: Exponential backoff factor for retries (default: 2.0).
     - `CODEXMCP_USE_CLI`: Whether to use Codex CLI when available (default: true).

## Usage

### Running the Server

Start the CodexMCP server with one simple command:

```bash
python -m codexmcp.server
```

or use the convenient entry point:

```bash
codexmcp
```

The server will start listening on port 8080 (by default). Your applications can now make requests to the server's API endpoints.

### Developer Notes

If you're developing or extending CodexMCP, be aware of these implementation details:

1. **Prompt Templates**: All prompt templates are stored in the `src/codexmcp/prompt_files/` directory and are loaded lazily when first needed. If you want to add custom templates, add `.txt` files to this directory.

2. **o4-mini Model Support**: The system has special handling for the `o4-mini` model, including proper configuration of `max_completion_tokens` and temperature settings (temperature is always set to 1.0 for o4-mini).

3. **CLI Integration**: As of version 0.1.5, CodexMCP now uses a dedicated `cli_backend` module for all Codex CLI interactions, executed per-call rather than through a long-lived pipe. This improves reliability and simplifies the architecture.

4. **Custom Templates**: To add custom templates, place them in `src/codexmcp/templates/` with a `.txt` extension. Templates use Python's standard string formatting with named placeholders like `{parameter_name}`.

### How It Works

1. **Your Application** makes a request to a specific CodexMCP endpoint (like `/tools/generate_code`)
2. **CodexMCP Server** processes the request and sends it to the Codex CLI
3. **Codex CLI** generates the requested code or documentation with filesystem context awareness
4. **CodexMCP Server** returns the result to your application

This approach gives you the power of AI coding assistance while keeping your application in control of when and how to use it.

### Available Tools

CodexMCP provides the following AI-powered tools:

#### Core Tools

1. **generate_code**: Generate code in any programming language
   - `description`: Task description
   - `language`: Programming language (default: "Python")
   - `model`: OpenAI model to use (default: "o4-mini")

2. **assess_code**: Evaluate and improve existing code
   - `code`: Optional source code to assess (if omitted, analyzes workspace)
   - `language`: Programming language (default: "Python")
   - `focus_areas`: Optional list of areas to focus on
   - `extra_prompt`: Optional free-form instructions
   - `model`: OpenAI model to use (default: "o4-mini")

3. **explain**: Provide context-aware code explanations
   - First argument: Optional code snippet or file path
   - `audience`: Target audience (default: "developer")
   - `detail_level`: Level of detail (default: "medium")
   - `model`: OpenAI model to use (default: "o4-mini")

4. **write_tests**: Generate unit tests
   - `code`: Optional source code to test (if omitted, analyzes workspace)
   - `description`: Additional testing requirements
   - `model`: OpenAI model to use (default: "o4-mini")

5. **migrate_code**: Migrate code between different versions or frameworks
   - `code`: Optional source code to migrate (if omitted, analyzes workspace)
   - `from_version`: Source version/framework (e.g., "Python 2", "React 16")
   - `to_version`: Target version/framework (e.g., "Python 3", "React 18")
   - `language`: Base programming language (default: "Python")
   - `model`: OpenAI model to use (default: "o4-mini")

6. **generate_docs**: Create documentation for code
   - `code`: Optional source code to document (if omitted, analyzes workspace)
   - `doc_format`: Output format ("docstring", "markdown", "html")
   - `model`: OpenAI model to use (default: "o4-mini")

7. **write_openai_agent**: Generate an OpenAI Agent implementation
   - `name`: Agent name
   - `instructions`: Agent system prompt
   - `tool_functions`: List of tool descriptions
   - `description`: Additional agent details
   - `model`: OpenAI model to use (default: "o4-mini")

All tools now leverage the filesystem context awareness of the Codex CLI, allowing them to work with the current project's files and directory structure even when no code is explicitly provided.

### Deprecated Tools

The following tools are deprecated and will be removed in a future version:

1. **refactor_code**: Deprecated in favor of `assess_code_quality` and `migrate_code`
   - For code quality improvements, use `assess_code_quality`
   - For version/framework migrations, use `migrate_code`

2. **explain_code**: Deprecated in favor of `explain_code_for_audience`
   - Use `explain_code_for_audience` with appropriate audience and detail level parameters

### Example Client

```python
import asyncio
from fastmcp import MCPClient

async def main():
    client = MCPClient("http://localhost:8080")
    
    # Generate some Python code
    code = await client.generate_code(
        description="Create a function to calculate Fibonacci numbers",
        language="Python"
    )
    print("Generated code:")
    print(code)
    
    # Assess code quality
    quality_assessment = await client.assess_code(
        code=code,
        language="Python",
        focus_areas=["performance", "readability"]
    )
    print("\nCode quality assessment:")
    print(quality_assessment)
    
    # Generate tests
    tests = await client.write_tests(
        code=code,
        description="Include tests for edge cases like negative numbers"
    )
    print("\nGenerated tests:")
    print(tests)
    
    # Explain code for different audiences
    explanation = await client.explain(
        code,
        audience="beginner",
        detail_level="detailed"
    )
    print("\nCode explanation for beginners:")
    print(explanation)
    
    # Generate documentation
    docs = await client.generate_docs(
        code=code,
        doc_format="markdown"
    )
    print("\nMarkdown documentation:")
    print(docs)
    
    # Generate an OpenAI agent
    agent_code = await client.write_openai_agent(
        name="MathHelper",
        instructions="You are a helpful math assistant that helps solve mathematical problems.",
        tool_functions=["calculate", "plot_function", "solve_equation"]
    )
    print("\nOpenAI Agent Implementation:")
    print(agent_code)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

CodexMCP includes several advanced features to enhance reliability and performance:

### Response Caching

Identical prompts are automatically cached to improve response time and reduce API costs:

- Set `CODEXMCP_CACHE_ENABLED=0` to disable caching
- Configure cache timeout with `CODEXMCP_CACHE_TTL=3600` (in seconds)

### Error Handling & Retries

The system automatically handles errors with improved diagnostics:

- Error IDs are included in error messages for easier debugging
- Specific error types help diagnose issues

### Streamlined CLI Integration

All tools now use a dedicated `cli_backend` module for Codex CLI interactions:

- Per-call CLI execution instead of long-lived pipe for improved reliability
- Automatic filesystem context awareness for all tools
- Better error handling and logging

## Troubleshooting

### Common Issues

1. **"Codex executable path not configured or found"**
   - Ensure the Codex CLI is installed globally with `npm install -g @openai/codex`
   - Set `CODEX_PATH` environment variable if the binary is in a non-standard location

2. **API Key Issues**
   - Make sure your `OPENAI_API_KEY` is set in the environment or `.env` file
   - Check that the key has the correct permissions and hasn't expired

3. **Model Availability**
   - If you see "Model unavailable" errors, check that the specified model exists and is available in your OpenAI account
   - You can specify a different model with the `CODEX_MODEL` environment variable

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run a specific test
pytest tests/test_tools.py::TestGenerateCode

# Test with coverage
pytest --cov=codexmcp
```

## License

MIT
