# CodexMCP

Minimal **FastMCP** server that wraps the OpenAI **Codex CLI** and makes the
model available over standard‑I/O so it can be consumed with `mcp‑cli` (or any
other MCP‑compatible client).

Tools exposed by this server (all asynchronous):

1. `generate_code(description, language="Python", model="o4-mini")`
2. `refactor_code(code, instruction, model="o4-mini")`
3. `write_tests(code, description="", model="o4-mini")`
4. `explain_code(code, detail_level="medium", model="o4-mini")`
5. `generate_docs(code, doc_format="docstring", model="o4-mini")`

Everything that the Codex subprocess prints (stdout **and** stderr) is recorded
to `~/.codexmcp/logs/` with rotation (5 files × 5 MiB).

---

## Installation (Linux/macOS)

### Prerequisites

1. Install Node 18 LTS and the Codex CLI globally:

```bash
npm install -g @openai/codex
```

2. Create a `.env` file in your working directory:

```ini
OPENAI_API_KEY=sk-<your-key>
```

### Install CodexMCP

Install using pip:

```bash
pip install codexmcp
```

Alternatively, install the latest version directly from GitHub:

```bash
pip install "git+https://github.com/tomascupr/codexMCP.git#egg=codexmcp"
```

---

## Running the server

Once installed, you can start the server in one of two ways:

- Using the console script:

  ```bash
  codexmcp
  ```

- Using Python's module mode:

  ```bash
  python -m codexmcp.server
  ```

The first request may take a couple of seconds while the model warms up; after
that each call returns in ~0.5‑1.5 s.

---

## Using `mcp-cli`

```bash
# List available tools (smoke-test: should answer <2 s)
 mcp-cli chat --server CodexMCP -q '["list_tools"]'

# Ask Codex to write a Rust hello-world program
mcp-cli chat --server CodexMCP -q \
    'mcp__CodexMCP__generate_code("hello world", "Rust")'

# Get an explanation of code
mcp-cli chat --server CodexMCP -q \
    'mcp__CodexMCP__explain_code("def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)", "brief")'
```

### API examples

```bash
# Refactor some code
mcp-cli chat --server CodexMCP -q \
  'mcp__CodexMCP__refactor_code("print(1+1)", "convert to a function")'

# Generate PyTest tests
mcp-cli chat --server CodexMCP -q \
  'mcp__CodexMCP__write_tests("def fib(n): return 1 if n<2 else fib(n-1)+fib(n-2)")'
```

---

## Troubleshooting

• `codex: command not found` → ensure npm's global bin directory is on `$PATH`.
• `.env` warnings → make sure your `.env` file is in your working directory.
• Logs not written → check permissions for `~/.codexmcp`.
• Long delay before first answer → normal, model container has to warm up.

## Testing

Run the test suite with pytest:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=codexmcp

# Run specific test file
pytest tests/test_tools.py
```

---

## License

MIT‑0 – see *LICENSE* if present.
