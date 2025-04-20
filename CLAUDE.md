# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Install: `pip install -e .` or `pip install -r requirements.txt`
- Run server: `python -m codexmcp.server` or `codexmcp`
- Testing: No formal test framework found - use `python -m unittest discover` if adding tests

## Code Style Guidelines
- Python version: 3.10+
- Imports: Group standard lib, third-party, then local imports with empty lines between
- Type hints: Use throughout (Union as | in Python 3.10+)
- Error handling: Use specific exceptions, log errors with logger from logging_cfg
- Naming: snake_case for variables/functions, CamelCase for classes
- Logging: Use logger from logging_cfg.py for all logging
- Docstrings: Use triple double-quotes with reST style
- Async: Use async/await pattern consistently in tool implementations
- Model parameter: Default to "o4-mini" but allow overrides

## Git Guidelines
- NEVER include Claude as a co-author in git commits

## mem0 Integration

[mem0](https://github.com/mem0ai/mem0) is a memory system for AI that can be integrated with this project.

### Overview
mem0 provides memory persistence, semantic search, and query capabilities for AI assistants. It allows the project to store and retrieve information across sessions using vector embeddings.

### Key Features
- **Persistent memory store**: Store important information between server restarts
- **Semantic search**: Find relevant information through embeddings
- **Fine-grained control**: Add, update, and delete memories with simple API calls
- **Efficient retrieval**: Query memories with relevance scoring

### Implementation Notes
- Use `mem0.MemoryStore` for creating a new memory store
- Generate embeddings with `mem0.embed_text("your text")`
- Store memories with `memory_store.add(memories)`
- Retrieve with `memory_store.query(query_text, limit=5)`
- See the [mem0 documentation](https://docs.mem0.ai/overview) for detailed usage examples

### Example Integration
```python
import mem0

# Create a memory store
memory_store = mem0.MemoryStore(name="codexmcp-memories")

# Add a memory
memory_store.add([
    {"text": "Added explain_code tool on April 21, 2025", "metadata": {"type": "feature"}}
])

# Query memories by relevance
results = memory_store.query("When was code explanation added?")
```

For more information, refer to the [mem0 documentation](https://docs.mem0.ai/overview) and [GitHub repository](https://github.com/mem0ai/mem0).