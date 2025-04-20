"""Unit tests for codexmcp tools module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastmcp import Context

from codexmcp.tools import (
    _query_codex,
    generate_code,
    refactor_code,
    write_tests,
    explain_code,
    generate_docs,
)


class TestQueryCodex:
    """Tests for the internal _query_codex function."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools.pipe")
    async def test_query_codex_success(self, mock_pipe):
        """Test successful query to codex."""
        # Setup mock
        mock_pipe.send = AsyncMock()
        mock_pipe.recv = AsyncMock(return_value='{"completion": "test response"}')

        # Create mock context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.progress = MagicMock()

        # Call the function
        result = await _query_codex(mock_ctx, "test prompt")

        # Assertions
        mock_pipe.send.assert_called_once_with({"prompt": "test prompt", "model": "o4-mini"})
        mock_pipe.recv.assert_called_once()
        assert result == "test response"

    @pytest.mark.asyncio
    @patch("codexmcp.tools.pipe", None)
    async def test_query_codex_no_pipe(self):
        """Test _query_codex with no pipe initialized."""
        mock_ctx = MagicMock(spec=Context)

        with pytest.raises(Exception):
            await _query_codex(mock_ctx, "test prompt")

    @pytest.mark.asyncio
    @patch("codexmcp.tools.pipe")
    async def test_query_codex_json_error(self, mock_pipe):
        """Test _query_codex with invalid JSON response."""
        # Setup mock
        mock_pipe.send = AsyncMock()
        mock_pipe.recv = AsyncMock(return_value='invalid json')

        # Create mock context
        mock_ctx = MagicMock(spec=Context)

        # Call the function and expect exception
        with pytest.raises(Exception):
            await _query_codex(mock_ctx, "test prompt")


class TestGenerateCode:
    """Tests for the generate_code tool."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools._query_codex")
    async def test_generate_code(self, mock_query_codex):
        """Test generate_code with default parameters."""
        # Setup
        mock_query_codex.return_value = "def example(): pass"
        mock_ctx = MagicMock(spec=Context)

        # Call the function
        result = await generate_code(mock_ctx, "Create an empty function")

        # Assertions
        assert result == "def example(): pass"
        mock_query_codex.assert_called_once()
        # Check prompt contains essential elements
        prompt = mock_query_codex.call_args[0][1]
        assert "Task: Code Generation" in prompt
        assert "You are an expert Python developer" in prompt
        assert "Create an empty function" in prompt

    @pytest.mark.asyncio
    @patch("codexmcp.tools._query_codex")
    async def test_generate_code_custom_language(self, mock_query_codex):
        """Test generate_code with custom language."""
        # Setup
        mock_query_codex.return_value = "function example() {}"
        mock_ctx = MagicMock(spec=Context)

        # Call the function
        result = await generate_code(mock_ctx, "Create an empty function", "JavaScript")

        # Assertions
        assert result == "function example() {}"
        prompt = mock_query_codex.call_args[0][1]
        assert "You are an expert JavaScript developer" in prompt


class TestRefactorCode:
    """Tests for the refactor_code tool."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools._query_codex")
    async def test_refactor_code(self, mock_query_codex):
        """Test refactor_code function."""
        # Setup
        mock_query_codex.return_value = "def improved(): return True"
        mock_ctx = MagicMock(spec=Context)
        code = "def test(): return 1"
        instruction = "Make it return True"

        # Call the function
        result = await refactor_code(mock_ctx, code, instruction)

        # Assertions
        assert result == "def improved(): return True"
        mock_query_codex.assert_called_once()
        prompt = mock_query_codex.call_args[0][1]
        assert "Task: Code Refactoring" in prompt
        assert "You are a software architect" in prompt
        assert code in prompt
        assert instruction in prompt


# Remove unittest-specific code