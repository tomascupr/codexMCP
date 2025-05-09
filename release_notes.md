### Added
- Lazy loading of prompt templates to improve startup performance
- Special handling for `o4-mini` model with optimized parameters
- Developer notes section in README.md

### Changed
- Moved prompt templates from `src/codexmcp/prompts/` to `src/codexmcp/prompt_files/`
- Simplified JSON processing in `_query_codex_via_pipe` function
- Improved `LLMClient` to better handle different OpenAI models
- Modified package imports to avoid premature loading 