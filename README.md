# CodexMCP

Minimal **FastMCP** server that wraps the OpenAI **Codex CLI** and makes the
model available over standard‑I/O so it can be consumed with `mcp‑cli` (or any
other MCP‑compatible client).

Tools exposed by this server (all asynchronous):

1. `generate_code(description, language="Python", model="o4-mini")`
2. `refactor_code(code, instruction, model="o4-mini")`
3. `write_tests(code, description="", model="o4-mini")`

Everything that the Codex subprocess prints (stdout **and** stderr) is recorded
to `~/.codexmcp/logs/` with rotation (5 files × 5 MiB).

---

## Installation (Linux/macOS)

### Prerequisites

1. Install Node 18 LTS and the Codex CLI globally:

```bash
npm install -g @openai/codex
```

2. Create a Python 3.10+ virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Create a `.env` file in your working directory:

```ini
OPENAI_API_KEY=sk-<your-key>
```

### Install CodexMCP

Install directly from GitHub:

```bash
pip install "git+https://github.com/tomascupr/codexMCP.git#egg=codexmcp"
```

Or, if published to PyPI (future):

```bash
pip install codexmcp
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

---

## License

MIT‑0 – see *LICENSE* if present.
