# CodexMCP

[![PyPI version](https://badge.fury.io/py/codexmcp.svg)](https://badge.fury.io/py/codexmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minimal **FastMCP** server that wraps the OpenAI **Codex CLI** and makes the
model available over standard‑I/O so it can be consumed with `mcp‑cli` (or any
other MCP‑compatible client).

**This project is open-sourced under the MIT License. See the LICENSE file for details.**

Tools exposed by this server (all asynchronous):

1. `generate_code(description, language="Python", model="o4-mini")` - Generates code based on a `description`. `language` specifies the target language. `model` selects the OpenAI model (e.g., "gpt-4", "o4-mini", "o3").
2. `refactor_code(code, instruction, model="o4-mini")` - Refactors the given `code` based on an `instruction`. `model` selects the OpenAI model.
3. `write_tests(code, description="", model="o4-mini")` - Writes tests for the given `code`, optionally guided by a `description`. `model` selects the OpenAI model.
4. `explain_code(code, detail_level="medium", model="o4-mini")` - Explains the given `code`. `detail_level` controls verbosity ("brief", "medium", "detailed"). `model` selects the OpenAI model.
5. `generate_docs(code, doc_format="docstring", model="o4-mini")` - Generates documentation for the `code`. `doc_format` specifies the format (e.g., "docstring", "markdown"). `model` selects the OpenAI model.
6. `write_openai_agent(name, instructions, tool_functions=[], description="", model="o4-mini")` - Generates Python code for an agent using the `openai-agents` SDK. Takes agent `name`, `instructions`, a list of natural language `tool_functions` descriptions, and optional `description`. `model` selects the OpenAI model.

Everything that the Codex subprocess prints (stdout **and** stderr) is recorded
to `~/.codexmcp/logs/` with rotation (5 files × 5 MiB).

---

## Installation (Linux/macOS)

### Prerequisites

1. Install Node 18 LTS and the Codex CLI globally (see [OpenAI Codex CLI setup](https://github.com/openai/codex-cli#setup) for details):

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

---

## Running the server

Once installed, you can start the server in one of two ways:

- Using the console script:

  ```bash
  codexmcp
  ```

The first request may take a couple of seconds while the model warms up; after
that each call returns in ~0.5‑1.5 s.

---

## Troubleshooting

• `codex: command not found` → ensure npm's global bin directory is on `$PATH`.
• `.env` warnings → make sure your `.env` file is in your working directory.
• Logs not written → check permissions for `~/.codexmcp`.
• Long delay before first answer → normal, model container has to warm up.

## Testing

Run the test suite with pytest:

```bash
# Install the package in editable mode with test dependencies
pip install -e .[test]

# Run all tests
pytest

# Run with coverage report
pytest --cov=codexmcp

# Run specific test file
pytest tests/test_tools.py

# Run manual client test script to verify stdio connectivity
python tests/manual_client_test.py
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
