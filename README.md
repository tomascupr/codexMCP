# CodexMCP – Model Context Protocol wrapper around the OpenAI Codex CLI

CodexMCP exposes the raw power of *OpenAI Codex* to every Model Context Protocol
(MCP) client – **mcp‑cli**, **Claude Code** and friends – via three focused
tools:

* `generate_code` – *write brand‑new code from a natural‑language prompt*
* `refactor_code` – *rewrite existing code according to an instruction*
* `write_tests`  – *create tests for an existing code‑base*

All communication between the client and the server happens over **stdio**.

---

## Quick‑start

```bash
# 1. Clone the repository & enter it
git clone … && cd codexMCP

# 2. Run the bootstrap helper (Node 18 + Codex CLI + venv)
./setup.sh

# 3. Start the server
python -m codexMCP.server

#    The process keeps running and waits for an MCP client to connect.
```

### Talk to the server with *mcp‑cli*

```bash
# Install the reference CLI if you don't have it yet
pip install --upgrade mcp-cli

# Inspect the server and list tools
mcp-cli inspect --server CodexMCP

# Or start an interactive chat and type `/tools` then `/call generate_code …`

# One‑shot Rust code generation via *inspect* utility
mcp-cli inspect --server CodexMCP --call generate_code --json '{"description":"hello world","language":"Rust"}'
```

### Talk to the server with *Claude Code*

```bash
# One‑time registration
claude mcp add CodexMCP \
  --cmd python -m codexMCP.server \
  -e OPENAI_API_KEY

# Usage inside a chat with Claude ↴

User > mcp__CodexMCP__generate_code({
  "description": "web server that returns 'pong'",
  "language": "Go"
})
```

---

## Implementation details

* **`codexMCP.pipe`** spawns `codex --json --pipe` *once* and keeps the process
  alive for the whole life‑time of the Python server. Requests are serialised
  through an *asyncio* lock so the order of responses always matches the
  ordering mandated by MCP.
* **`codexMCP.tools`** contain the three public `@mcp.tool()` functions.  They
  do nothing but craft a prompt, forward it to the pipe helper and post‑process
  the JSON result.
* **`codexMCP.server`** is the 30‑line executable entry‑point: instantiate
  `FastMCP("CodexMCP")`, register the tools, run the stdio event‑loop – that’s
  it.
* **`codexMCP.logging_cfg`** routes *every* log line to
  `~/.codexmcp/logs/codexmcp.log` so nothing ever pollutes *stdout* / *stderr*
  (which are reserved for the MCP transport framing).

## Troubleshooting

* **The server does not start** → ensure `OPENAI_API_KEY` is exported and that
  the *Codex CLI* binary is on `$PATH` (`npm list -g | grep codex-cli`).
* **`mcp-cli` cannot find the server** → verify that the `name` field in
  `codexMCP.server` is **exactly** `"CodexMCP"` (it is case‑sensitive).
* **Timeouts** → big prompts may trigger the 10 second *still working* keep
  ‑alive. You can increase the SDK timeout via the usual MCP configuration
  knobs.

---

## Extending CodexMCP

Adding a new tool is trivial:

```python
from modelcontextprotocol import tool

from codexMCP.pipe import get_pipe


@tool()
async def summarise_code(code: str, *, ctx=None) -> str:  # noqa: D401
    prompt = f"Summarise the following code:\n\n{code}\n\nSummary:"
    result = await get_pipe().query({"prompt": prompt, "model": "o4-mini"}, ctx)
    return result["choices"][0]["text"].strip()
```

Import the module inside `codexMCP.server` or call `server.register_tools_module()`
manually and you’re done ✨.

---

© 2025 – MIT license (see `LICENSE`).
