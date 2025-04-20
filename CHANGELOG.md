# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-04-20

### Added

- Initial project structure with FastMCP server wrapping Codex CLI.
- Tools: `generate_code`, `refactor_code`, `write_tests`.
- Logging to `~/.codexmcp/logs/codexmcp.log`.
- Setup script (`setup.sh`).
- `.env` file support for `OPENAI_API_KEY` using `python-dotenv`.
- Versioning (`__version__` in `shared.py`) and this CHANGELOG file.

### Fixed

- Resolved circular import issue between `server.py` and `tools.py` by introducing `shared.py` for singletons.
- Corrected issues with tool registration not being recognized by `mcp-cli`.
- Improved handling of API key propagation to the Codex subprocess.
- Fixed various bugs related to server startup and `CodexPipe` initialization. 