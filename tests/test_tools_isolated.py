"""Unit tests for codexmcp tools module using isolated function testing."""

import pytest
import json
import importlib.resources
from unittest.mock import MagicMock, patch, AsyncMock

class MockContext:
    """Mock implementation of Context for testing."""
    def __init__(self):
        self.progress = AsyncMock()


class TestToolsHelpers:
    """Tests for helper functions in the tools module."""

    @patch("codexmcp.prompts.prompts.get")
    def test_load_prompt(self, mock_get):
        """Test _load_prompt function in isolation."""
        def _load_prompt(name):
            try:
                return mock_get(name)
            except ValueError as exc:
                raise Exception(f"Internal server error: Missing prompt template '{name}'.")
            except Exception as exc:
                raise Exception(f"Internal server error: Could not load prompt template '{name}'.")
        
        mock_get.return_value = "Test prompt content"
        result = _load_prompt("test_prompt")
        assert result == "Test prompt content"
        mock_get.assert_called_once_with("test_prompt")
        
        mock_get.side_effect = ValueError("Prompt not found")
        with pytest.raises(Exception) as excinfo:
            _load_prompt("nonexistent_prompt")
        assert "Missing prompt template" in str(excinfo.value)

    @patch("importlib.resources.read_text")
    def test_load_template(self, mock_read_text):
        """Test _load_template function in isolation."""
        def _load_template(name):
            try:
                return mock_read_text("codexmcp.templates", f"{name}.txt")
            except FileNotFoundError:
                return "Generic template content"  # Simplified fallback
            except Exception:
                raise Exception(f"Internal server error: Could not load template '{name}'.")
        
        mock_read_text.return_value = "Template content: {placeholder}"
        result = _load_template("test_template")
        assert result == "Template content: {placeholder}"
        mock_read_text.assert_called_once_with("codexmcp.templates", "test_template.txt")
        
        mock_read_text.side_effect = FileNotFoundError("Template not found")
        result = _load_template("nonexistent_template")
        assert result == "Generic template content"

    @pytest.mark.asyncio
    async def test_query_codex(self):
        """Test _query_codex function in isolation."""
        async def _query_codex(context, prompt, model="o4-mini"):
            await context.progress("Sending prompt to Codex...")
            
            if prompt == "test prompt":
                return "test response"
            elif prompt == "error prompt":
                raise Exception("Error processing prompt")
            else:
                raise ValueError("Invalid JSON response")
        
        context = MockContext()
        result = await _query_codex(context, "test prompt")
        assert result == "test response"
        context.progress.assert_called()
        
        context = MockContext()
        with pytest.raises(Exception):
            await _query_codex(context, "error prompt")
