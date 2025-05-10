# CodexMCP

[![PyPI version](https://badge.fury.io/py/codexmcp.svg)](https://badge.fury.io/py/codexmcp)
[![GitHub release](https://img.shields.io/github/v/release/tomascupr/codexMCP)](https://github.com/tomascupr/codexMCP/releases)

Current version: **0.1.6**

## What is CodexMCP?

CodexMCP is a service that gives your applications access to AI coding capabilities without needing to build complex integrations. It's a server that exposes powerful code-related AI tools through a simple, standardized API.

**Important:** CodexMCP is **not** an autonomous agent - it's a tool provider that responds to specific requests. Your application remains in control, making specific requests for code generation, refactoring, or documentation as needed.

Think of CodexMCP as a bridge between your application and OpenAI's powerful AI coding capabilities. You send structured requests to the server (like "generate Python code that sorts a list"), and it returns the requested code or documentation.

A minimal FastMCP server wrapping the [OpenAI Codex CLI](https://github.com/openai/codex) to provide AI code generation, refactoring, and documentation capabilities through a standardized API.

## New Features

CodexMCP has been enhanced with several key improvements:

### 1. Real-time Streaming Responses

The latest update enables real-time streaming of responses when using the OpenAI API. This provides immediate feedback as tokens are generated, significantly improving the user experience for all tools.

### 2. Streamlined Codex CLI Integration

The latest update removes the long-lived CodexPipe in favor of per-call CLI execution, improving reliability and simplifying the architecture. All tools now route through a new dedicated `cli_backend` module.

### 3. Simplified Tool Structure

The tools API has been reorganized for clarity and ease of use, with a focus on the most essential coding tasks:
- `code_generate`: Unified entry point for all code-generation tasks.
- `review_code`: Assess code quality, security, style or other aspects.
- `describe_codebase`: Explain the repository, a file, or a code snippet.

### 4. Context-Aware Code Analysis

The `describe_codebase` tool (when provided a file path) allows you to analyze code with awareness of its surrounding context.

### 5. Interactive Code Generation with Feedback Loop

The `code_generate` tool, when provided with feedback or an iteration count, enables an iterative approach to code generation, where you can provide feedback on previous iterations to refine the results.

### 6. Advanced Code Quality Assessment

The `review_code` tool provides detailed code quality assessments with actionable suggestions for improvement, focusing on specific areas like performance, readability, or security.

### 7. Audience-Targeted Code Explanations

The `describe_codebase` tool provides code explanations tailored to different audiences (developers, managers, beginners) with customizable detail levels.

### 8. Code Migration and Modernization

Functionality for code migration and modernization can be achieved using `code_generate` with appropriate descriptions.

### 9. Template-Based Code Generation

The `code_generate` tool, when provided a `template_name` and `parameters`, enables code generation using customizable templates, increasing productivity for common tasks.

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

3. **CLI Integration**: As of version 0.1.6, CodexMCP now uses a dedicated `cli_backend` module for all Codex CLI interactions, executed per-call rather than through a long-lived pipe. This improves reliability and simplifies the architecture.

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

1.  **`code_generate`**: Unified entry point for all code-generation tasks.
    - `description`: Task description.
    - `language`: (Optional) Programming language (default: "Python").
    - `template_name`: (Optional) Name of the template to use.
    - `parameters`: (Optional) Dictionary of parameters to fill in the template.
    - `feedback`: (Optional) Feedback on previous iterations.
    - `iteration`: (Optional) Current iteration number (default: 1).

2.  **`describe_codebase`**: Explain the repository, a file, or a code snippet.
    - `subject`: (Optional) Code snippet, file path, or concept to explain. If omitted, describes the current repository.
    - `audience`: (Optional) Target audience (default: "developer").
    - `detail_level`: (Optional) Level of detail (e.g., "brief", "medium", "detailed", default: "medium").

3.  **`review_code`**: Assess code quality, security, style or other aspects.
    - `code`: (Optional) Source code to assess. If omitted, the CLI might analyze the workspace based on the prompt.
    - `language`: (Optional) Programming language (default: "Python").
    - `focus_areas`: (Optional) List of areas to focus on (e.g., "security", "performance").
    - `extra_prompt`: (Optional) Free-form instructions to guide the review.

All tools leverage the filesystem context awareness of the Codex CLI when it's used, allowing them to work with the current project's files and directory structure. The `model` parameter can be passed to any tool to specify the OpenAI model to use (default: "o4-mini" or as configured).

### Example Client

```python
import asyncio
from fastmcp import MCPClient

async def main():
    # Ensure the server is running, e.g., by `python -m codexmcp.server`
    # or the `codexmcp` command.
    client = MCPClient("http://localhost:8080") # Default port
    
    # Generate some Python code
    generated_code = await client.code_generate(
        description="Create a function to calculate Fibonacci numbers recursively",
        language="Python"
    )
    print("Generated code:")
    print(generated_code)
    
    # Review the generated code
    quality_assessment = await client.review_code(
        code=generated_code,
        language="Python",
        focus_areas=["readability", "potential bugs"],
        extra_prompt="Consider Python best practices."
    )
    print("\nCode quality assessment:")
    print(quality_assessment)
        
    # Describe the generated code
    explanation = await client.describe_codebase(
        subject=generated_code, # Can also be a file path or general concept
        audience="beginner",
        detail_level="detailed"
    )
    print("\nCode explanation for beginners:")
    print(explanation)

    # Example: Generate code from a template
    # First, ensure you have a template, e.g., src/codexmcp/templates/simple_class.txt:
    # class {class_name}:
    #     def __init__(self, name):
    #         self.name = name
    #
    #     def greet(self):
    #         return f"Hello, {self.name}!"
    #
    # Note: The server needs to be able to find this template.
    # For a packaged installation, this means the template should be in the installed package.
    # For local development, ensure paths are correct relative to where server is run.
    try:
        templated_code = await client.code_generate(
            description="Generate a simple class using a template.", # Description is still useful context
            template_name="simple_class", # Name of the template file (without .txt)
            parameters={"class_name": "MyGreeter"},
            language="Python"
        )
        print("\nGenerated code from template 'simple_class':")
        print(templated_code)
    except Exception as e:
        # This might fail if the template isn't found by the server
        print(f"\nError generating code from template (ensure template exists and is accessible): {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

CodexMCP includes several advanced features to enhance reliability and performance:

### Real-time Streaming

API responses are streamed in real-time, displaying tokens as they're generated:

- Improves user experience with immediate feedback
- Shows progress for longer generations
- Works with all tools using the OpenAI API

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
