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

CodexMCP has been enhanced with several high-leverage improvements:

### 1. Context-Aware Code Analysis

The new `analyze_code_context` tool allows you to analyze code with awareness of its surrounding context, including related files. This provides deeper insights into how code fits into the broader architecture.

### 2. Interactive Code Generation with Feedback Loop

The `interactive_code_generation` tool enables an iterative approach to code generation, where you can provide feedback on previous iterations to refine the results.

### 3. Advanced Code Quality Assessment

The `assess_code_quality` tool provides detailed code quality assessments with actionable suggestions for improvement, focusing on specific areas like performance, readability, or security.

### 4. Intelligent Code Search

The `search_codebase` tool allows you to search and analyze code across multiple files using natural language queries, making it easier to navigate large codebases.

### 5. Audience-Targeted Code Explanations

The `explain_code_for_audience` tool provides code explanations tailored to different audiences (developers, managers, beginners) with customizable detail levels.

### 6. Code Migration and Modernization

The `migrate_code` tool helps you migrate code between different language versions or frameworks, with explanations of the changes made.

### 7. Template-Based Code Generation

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

3. **CLI Fallback**: The system tries to use the Codex CLI first for better performance, falling back to the OpenAI API when necessary.

4. **Custom Templates**: To add custom templates, place them in `src/codexmcp/templates/` with a `.txt` extension. Templates use Python's standard string formatting with named placeholders like `{parameter_name}`.

### How It Works

1. **Your Application** makes a request to a specific CodexMCP endpoint (like `/tools/generate_code`)
2. **CodexMCP Server** processes the request and sends it to the OpenAI model
3. **OpenAI Model** generates the requested code or documentation
4. **CodexMCP Server** returns the result to your application

This approach gives you the power of AI coding assistance while keeping your application in control of when and how to use it.

### Available Tools

CodexMCP provides the following AI-powered tools:

#### Core Code Generation Tools

1. **generate_code**: Generate code in any programming language
   - `description`: Task description
   - `language`: Programming language (default: "Python")
   - `model`: OpenAI model to use (default: "o4-mini")

2. **interactive_code_generation**: Generate code with an iterative feedback loop
   - `description`: Task description
   - `language`: Programming language (default: "Python")
   - `feedback`: Feedback on previous iterations
   - `iteration`: Current iteration number (default: 1)
   - `model`: OpenAI model to use (default: "o4-mini")

3. **generate_from_template**: Generate code using customizable templates
   - `template_name`: Name of the template to use
   - `parameters`: Dictionary of parameters to fill in the template
   - `language`: Programming language (default: "Python")
   - `model`: OpenAI model to use (default: "o4-mini")

#### Code Analysis Tools

4. **explain_code_for_audience**: Explain code with customized detail level for different audiences
   - `code`: Source code to explain
   - `audience`: Target audience (e.g., "developer", "manager", "beginner")
   - `detail_level`: Level of detail ("brief", "medium", "detailed")
   - `model`: OpenAI model to use (default: "o4-mini")

5. **assess_code_quality**: Assess code quality and provide improvement suggestions
   - `code`: Source code to assess
   - `language`: Programming language (default: "Python")
   - `focus_areas`: Specific areas to focus on (e.g., "performance", "readability", "security")
   - `model`: OpenAI model to use (default: "o4-mini")

6. **analyze_code_context**: Analyze code with awareness of its surrounding context
   - `code`: Source code to analyze
   - `file_path`: Path to the file containing the code (for context)
   - `surrounding_files`: List of related file paths to consider for context
   - `model`: OpenAI model to use (default: "o4-mini")

7. **search_codebase**: Search and analyze code across multiple files based on natural language query
   - `query`: Natural language search query
   - `file_patterns`: File patterns to include in search (default: ["*.py", "*.js", "*.ts"])
   - `max_results`: Maximum number of results to return (default: 5)
   - `model`: OpenAI model to use (default: "o4-mini")

#### Code Transformation Tools

8. **migrate_code**: Migrate code between different language versions or frameworks
   - `code`: Source code to migrate
   - `from_version`: Source version/framework (e.g., "Python 2", "React 16")
   - `to_version`: Target version/framework (e.g., "Python 3", "React 18")
   - `language`: Base programming language (default: "Python")
   - `model`: OpenAI model to use (default: "o4-mini")

9. **write_tests**: Generate unit tests for code
   - `code`: Source code to test
   - `description`: Additional testing requirements
   - `model`: OpenAI model to use (default: "o4-mini")

#### Documentation Tools

10. **generate_docs**: Create documentation for code
    - `code`: Source code to document
    - `doc_format`: Output format ("docstring", "markdown", "html")
    - `model`: OpenAI model to use (default: "o4-mini")

11. **generate_api_docs**: Generate API documentation or client code
    - `code`: API implementation code
    - `framework`: Web framework used (default: "FastAPI")
    - `output_format`: Output format ("openapi", "swagger", "markdown", "code")
    - `client_language`: Language for client code (when output_format is "code")
    - `model`: OpenAI model to use (default: "o4-mini")

#### Agent Generation Tools

12. **write_openai_agent**: Generate an OpenAI Agent implementation
    - `name`: Agent name
    - `instructions`: Agent system prompt
    - `tool_functions`: List of tool descriptions
    - `description`: Additional agent details
    - `model`: OpenAI model to use (default: "o4-mini")

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
    
    # Use interactive code generation with feedback
    improved_code = await client.interactive_code_generation(
        description="Create a function to calculate Fibonacci numbers",
        language="Python",
        feedback="The solution works but could be more efficient with memoization",
        iteration=2
    )
    print("\nImproved code with feedback:")
    print(improved_code)
    
    # Assess code quality
    quality_assessment = await client.assess_code_quality(
        code=improved_code,
        language="Python",
        focus_areas=["performance", "readability"]
    )
    print("\nCode quality assessment:")
    print(quality_assessment)
    
    # Generate API documentation
    api_code = """
    from fastapi import FastAPI, Query
    
    app = FastAPI()
    
    @app.get("/items/")
    async def read_items(q: str = Query(None, min_length=3, max_length=50)):
        results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
        if q:
            results["items"] = [item for item in results["items"] if q in item["item_id"]]
        return results
    """
    
    # Explain code for different audiences
    explanation = await client.explain_code_for_audience(
        code=api_code,
        audience="manager",
        detail_level="brief"
    )
    print("\nCode explanation for managers:")
    print(explanation)
    
    # Generate API documentation
    docs = await client.generate_api_docs(
        code=api_code,
        framework="FastAPI",
        output_format="openapi"
    )
    print("\nAPI documentation:")
    print(docs)
    
    # Generate code from template
    template_code = await client.generate_from_template(
        template_name="api_endpoint",
        parameters={
            "endpoint_name": "create_user",
            "http_method": "POST",
            "path": "/users",
            "description": "Create a new user in the system",
            "request_params": "username: str, email: str, password: str",
            "response_format": "JSON with user ID and creation timestamp"
        },
        language="Python"
    )
    print("\nTemplate-based code generation:")
    print(template_code)

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

The system automatically retries failed API calls with exponential backoff:

- Configure with `CODEXMCP_MAX_RETRIES=3` and `CODEXMCP_RETRY_BACKOFF=2.0`
- Error IDs are included in error messages for easier debugging
- Specific error types help diagnose issues (rate limits, timeouts, etc.)

### Provider Flexibility

Choose between Codex CLI and direct API access:

- Set `CODEXMCP_USE_CLI=0` to force using the API even when CLI is available
- Direct API access includes streaming support and better error handling

## Troubleshooting

### Common Issues

1. **"Codex executable path not configured or found"**
   - Ensure the Codex CLI is installed globally with `npm install -g @openai/codex`

2. **API Key Issues**
   - Make sure your `OPENAI_API_KEY` is set in the environment or `.env` file
   - Check that the key has the correct permissions and hasn't expired

3. **Model Availability**
   - If you see "Model unavailable" errors, check that the specified model exists and is available in your OpenAI account


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
