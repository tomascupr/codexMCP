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

The helper script below installs Node 18 LTS, the Codex CLI, creates a Python
3.10 `venv` and installs the required PyPI packages.

```bash
git clone <repo‑url> codexmcp
cd codexmcp

# Needs sudo for the Node 18 APT repo – omit if Node 18 LTS is already present.
./setup.sh

# ➊ Create an OpenAI API key and export it so the CLI can authenticate
export OPENAI_API_KEY="sk‑<your‑key>"

# ➋ Activate the virtual‑env for the current shell (*optional* – convenience)
source .venv/bin/activate

# ➌ Run the server (responds on stdin/stdout)
python server.py
```

The first request may take a couple of seconds while the model warms up; after
that each call returns in ~0.5‑1.5 s.

---

## Using `mcp‑cli`

```bash
# List available tools (smoke‑test: should answer <2 s)
mcp-cli chat --server CodexMCP -q '["list_tools"]'

# Ask Codex to write a Rust hello‑world program
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

• `codex: command not found` → run `npm i -g @openai/codex`, ensure
  npm’s *global* bin directory is on `$PATH`.
• Logs not written → check permissions for `~/.codexmcp`.
• Long delay before first answer → normal, model container has to warm‑up.

---

## License

MIT‑0 – see *LICENSE* if present.
