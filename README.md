# CodexMCP

## What is CodexMCP?

CodexMCP is a service that gives your applications access to AI coding capabilities without needing to build complex integrations. It's a server that exposes powerful code-related AI tools through a simple, standardized API.

**Important:** CodexMCP is **not** an autonomous agent - it's a tool provider that responds to specific requests. Your application remains in control, making specific requests for code generation, refactoring, or documentation as needed.

Think of CodexMCP as a bridge between your application and OpenAI's powerful AI coding capabilities. You send structured requests to the server (like "generate Python code that sorts a list"), and it returns the requested code or documentation.

A minimal FastMCP server wrapping the [OpenAI Codex CLI](https://github.com/openai/code-interpreter) to provide AI code generation, refactoring, and documentation capabilities through a standardized API.

## Installation

1. **Prerequisites**:
   - Node.js 18 LTS or later
   - Python 3.10 or later
   - [Codex CLI](https://github.com/openai/codex) installed globally:
     ```bash
     npm install -g @openai/codex
     ```

2. **Install CodexMCP**:
   ```bash
   pip install -e .
   ```
   
   For development, install with test dependencies:
   ```bash
   pip install -e .[test]
   ```

3. **Environment Setup**:
   - Create a `.env` file in your project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=sk-your-key-here
     ```
   - Optional environment variables:
     - `CODEXMCP_DEFAULT_MODEL`: Default model to use (default: "o4-mini")
     - `CODEXMCP_LOG_LEVEL`: Logging level (default: INFO)
     - `CODEXMCP_CONSOLE_LOG`: Enable console logging (default: true)

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

### How It Works

1. **Your Application** makes a request to a specific CodexMCP endpoint (like `/tools/generate_code`)
2. **CodexMCP Server** processes the request and sends it to the OpenAI model
3. **OpenAI Model** generates the requested code or documentation
4. **CodexMCP Server** returns the result to your application

This approach gives you the power of AI coding assistance while keeping your application in control of when and how to use it.

### Available Tools

CodexMCP provides the following AI-powered tools:

1. **generate_code**: Generate code in any programming language
   - `description`: Task description
   - `language`: Programming language (default: "Python")

2. **refactor_code**: Improve existing code
   - `code`: Source code to refactor
   - `instruction`: How to refactor the code

3. **write_tests**: Generate unit tests for code
   - `code`: Source code to test
   - `description`: Additional testing requirements

4. **explain_code**: Explain code functionality and structure
   - `code`: Source code to explain
   - `detail_level`: Level of detail ("brief", "medium", "detailed")

5. **generate_docs**: Create documentation for code
   - `code`: Source code to document
   - `doc_format`: Output format ("docstring", "markdown", "html")

6. **write_openai_agent**: Generate an OpenAI Agent implementation
   - `name`: Agent name
   - `instructions`: Agent system prompt
   - `tool_functions`: List of tool descriptions
   - `description`: Additional agent details

7. **generate_api_docs**: Generate API documentation or client code
   - `code`: API implementation code
   - `framework`: Web framework used (default: "FastAPI")
   - `output_format`: Output format ("openapi", "swagger", "markdown", "code")
   - `client_language`: Language for client code (when output_format is "code")

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
    print(code)
    
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
    
    docs = await client.generate_api_docs(
        code=api_code,
        framework="FastAPI",
        output_format="openapi"
    )
    print(docs)

if __name__ == "__main__":
    asyncio.run(main())
```

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
