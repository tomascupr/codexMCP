# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2025-05-09

### Added
- Lazy loading of prompt templates to improve startup performance
- Special handling for `o4-mini` model with optimized parameters
- Developer notes section in README.md

### Changed
- Moved prompt templates from `src/codexmcp/prompts/` to `src/codexmcp/prompt_files/`
- Simplified JSON processing in `_query_codex_via_pipe` function
- Improved `LLMClient` to better handle different OpenAI models
- Modified package imports to avoid premature loading

## [0.1.4] - 2025-04-23

### Added

- New tool: `generate_api_docs` for creating API documentation:
  - Generate OpenAPI 3.0 specifications in YAML format
  - Generate Swagger 2.0 specifications in JSON format
  - Create detailed markdown API documentation
  - Generate client code based on API definitions
- Two new tools:
  - `explain_code`: Explains code at various detail levels ("brief", "medium", "detailed")
  - `generate_docs`: Generates documentation in different formats ("docstring", "markdown", "html")
- Comprehensive test suite:
  - Unit tests for all core modules (tools, pipe, server, shared)
  - Test fixtures and configurations
  - Coverage reporting setup
  - Testing documentation in README
- New tool: `write_openai_agent` for generating OpenAI Agents SDK code.
- Manual client test script (`tests/manual_client_test.py`) to verify server connectivity and tool listing over stdio.

### Changed

- Enhanced all tool prompts with:
  - Role-playing elements (e.g., "You are an expert developer...")
  - Specific guidelines for quality, formatting, and edge cases
  - Improved structure with clear sections
  - More detailed instructions for better outputs
- Added pytest configuration in pyproject.toml
- Updated requirements.txt with test dependencies

## [0.1.2] - 2025-04-20

### Added

- Setup for PyPI publishing using `build` and `twine`.
- Configured `.pypirc`

## [0.1.1] - 2025-04-20

### Added

- Restructured project to use the `src/` layout with `pyproject.toml` packaging
- Added `codexmcp` console script entry point via `[project.scripts]`

### Changed

- Updated imports to use package-relative paths within `codexmcp` namespace
- Bumped package version to 0.1.1

### Fixed

- Added `main()` function in `server.py` for module entry point
- Improved `.env` loading to check current directory first and warned if missing
- Resolved `ImportError` issues for `logging_cfg`, `shared`, and `tools` modules

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