# CodexMCP – Development Guide

This document is aimed at **contributors and maintainers** who need to look
under the hood of CodexMCP, debug issues, or extend its functionality.  It
collects the tribal knowledge that is too low-level for the public README but
essential for productive development.

---

## 0. Terminology & Positioning

| Term | Meaning |
|------|---------|
| **MCP** | *Model-Calling-Protocol* – JSON messages that describe tool calls and their results.  See the `mcp` / `fastmcp` packages. |
| **FastMCP** | Convenience wrapper around `mcp` that gives a Pythonic `@mcp.tool` decorator and an event-loop runner. |
| **CodexMCP** | A FastMCP **server** that exposes code-centric tools and routes the heavy lifting to the OpenAI Codex **CLI** (preferred) or the OpenAI chat **API** (fallback). |

---

## 1. Code Layout

```
src/codexmcp/
    shared.py          # boots singletons: logger, config, FastMCP instance, CodexPipe
    server.py          # real entry-point – imports shared, then tools, then mcp.run()
    tools.py           # ~25 @mcp.tool coroutines (generate_code, assess_code_quality …)
    pipe.py            # async wrapper around long-lived `codex --pipe` subprocess
    client.py          # OpenAI SDK fallback with cache & retry
    prompts.py         # loads *.txt prompt templates once at start-up
    prompts/*.txt      # human-written prompt templates
    templates/*.txt    # generic code-generation templates (e.g., API endpoint)
    logging_cfg.py     # rotating file+console log setup
    config.py          # env-var → config singleton
    exceptions.py      # thin error hierarchy on top of FastMCP’s ToolError
README.md              # public user docs (high-level)
DEVELOPMENT.md         # ← **this file** (low-level details)
tests/                 # pytest suite using heavy mocking
```

---

## 2. Boot Sequence (what runs first?)

1. **`python -m codexmcp.server`** (or the `codexmcp` entry-point) is executed.
2. `server.py` imports **`shared.py`** – *all singletons are initialised here*:
   - `.env` file is loaded (if present).
   - Logging is configured (rotating file + optional console).
   - `mcp = FastMCP("CodexMCP")` is created.
   - `client = LLMClient()` (OpenAI SDK wrapper) is created.
   - The system tries to locate the **`codex`** executable.  
     • Found  → start a **CodexPipe** subprocess with `--json --pipe` flags.  
     • Not found → `pipe = None` (forces API fallback later).
3. Back in `server.py` the **`tools`** module is imported.  Each `@mcp.tool`
   decorator registers a function with the FastMCP server.
4. Finally `mcp.run()` starts the stdio event-loop.  The process now listens
   indefinitely for MCP JSON messages.

---

## 3. Runtime Call Flow

```
client → (JSON) → FastMCP → tools.generate_code() → _query_codex() ─►
                                               ├─ CodexPipe (CLI) → result
                                               └─ LLMClient (API) ─┘
```

1. A *call* message arrives, e.g.

   ```jsonc
   { "id": 1, "type": "call", "tool": "generate_code",
     "args": { "description": "Return nth Fibonacci", "language": "Python" } }
   ```
2. FastMCP dispatches to `codexmcp.tools.generate_code(ctx, …)`.
3. The tool expands `prompts/generate_code.txt` with `.format()`.
4. It awaits `_query_codex(ctx, prompt, model)` which chooses the execution
   backend:
   - **CLI path**: `pipe.send({prompt, model})` then `pipe.recv()` → JSON with
     `completion | text | response` field.
   - **API path**: `LLMClient.generate(prompt, model=…, temp=…, max_tokens=…)`
     (three retries, SHA-256 cache).
5. The coroutine returns a plain-text answer which FastMCP wraps in a
   *result* message and writes to stdout.

---

## 4. Two Inference Back-ends

### 4.1 Codex CLI (preferred)

* A single Node process started with:

  ```bash
  codex --json --pipe -q Hello --approval-mode=full-auto --disable-shell --exit-when-idle
  ```

* `CodexPipe` keeps stdin/stdout open for the lifetime of the server, with a
  dedicated thread that drains and de-ANSI-fies **stderr**.

### 4.2 OpenAI ChatCompletion API (fallback)

* Used when the CLI is missing or crashes.
* `LLMClient` is a singleton wrapper around `openai.AsyncOpenAI`.
* Adds 1-hour in-memory cache and exponential-backoff retries.

---

## 5. Prompt & Template System

`PromptManager` loads every `prompts/*.txt` file once into a dict and provides
`prompts.get(name, **vars)` – very fast and avoids file-I/O in hot paths.
`templates/*.txt` are longer code skeletons used by the
`generate_from_template` tool.

---

## 6. Configuration (env-vars)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CODEXMCP_DEFAULT_MODEL`       | `o4-mini` | model name passed to CLI / API |
| `CODEXMCP_DEFAULT_TEMP`        | `0.2`     | temperature for API fallback   |
| `CODEXMCP_DEFAULT_MAX_TOKENS`  | `4096`    | max_tokens for API fallback    |
| `CODEXMCP_CACHE_ENABLED`       | `1`       | enable in-memory cache         |
| `CODEXMCP_CACHE_TTL`           | `3600`    | cache TTL in seconds           |
| `CODEXMCP_MAX_RETRIES`         | `3`       | API retry attempts             |
| `CODEXMCP_RETRY_BACKOFF`       | `2.0`     | exponential backoff factor     |
| `CODEXMCP_CONSOLE_LOG`         | `1`       | show logs on stdout            |
| `CODEXMCP_USE_CLI`             | `1`       | disable CLI if set to `0`      |
| `OPENAI_API_KEY`               | –         | required for API fallback      |

---

## 7. Error Handling

`exceptions.py` defines specialised subclasses of `fastmcp.exceptions.ToolError`:

* `CodexRateLimitError`
* `CodexTimeoutError`
* `CodexModelUnavailableError`
* `CodexConnectionError`

Each one carries an 8-char `error_id` for cross-referencing with the logs.

---

## 8. Logging

* Rotating file logs in `~/.codexmcp/logs/codexmcp.log` (5 × 5 MiB).
* Same messages optionally echoed to console (`CODEXMCP_CONSOLE_LOG=1`).
* Every request/response line and stderr output of the Codex CLI is recorded.

---

## 9. Tests

The `tests/` directory contains a pytest suite that mocks external
dependencies so that no real OpenAI traffic or CLI processes are required.
Long-running or OS-specific scenarios are marked `pytest.skip` to keep CI fast.

---

## 10. Example MCP Call (raw JSON)

```jsonc
// initialize handshake
{ "id": 0, "type": "initialize" }

// call generate_code
{ "id": 1, "type": "call", "tool": "generate_code",
  "args": { "description": "Return nth Fibonacci", "language": "Python" } }

// server replies
{ "id": 1, "type": "progress", "content": "Generating response…" }
{ "id": 1, "type": "result",
  "content": "def fibonacci(n: int) -> int:\n    …" }
```

If you prefer a friendly CLI wrapper use:

```bash
mcp-cli call CodexMCP generate_code \
  --description "Return nth Fibonacci" --language Python
```

---

Happy hacking!  If anything in this document falls out of sync with the code
please update it – **this file is the canonical knowledge base for CodexMCP
internals.**
