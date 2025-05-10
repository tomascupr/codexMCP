"""Unit tests for codexmcp tools module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from fastmcp import Context

from codexmcp.tools import (
    _query_codex,
    code_generate,
    review_code,
    describe_codebase,
)


class TestQueryCodex:
    """Tests for the internal _query_codex function using the CLI backend."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools.cli_backend.query_cli", new_callable=AsyncMock)
    async def test_query_codex_success_cli(self, mock_query_cli):
        """Test that _query_codex uses the CLI backend."""
        mock_query_cli.return_value = "cli response"
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.progress = AsyncMock()

        result = await _query_codex(mock_ctx, "test prompt", model="o4-mini")

        mock_query_cli.assert_awaited_once()
        assert result == "cli response"

    @pytest.mark.asyncio
    @patch("codexmcp.tools.cli_backend.query_cli", side_effect=Exception("CLI error"))
    @patch("codexmcp.tools.shared.client.generate", new_callable=AsyncMock)
    async def test_query_codex_api_fallback(self, mock_generate, mock_query_cli):
        """Test that _query_codex falls back to the API when CLI errors."""
        mock_generate.return_value = "api response"
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.progress = AsyncMock()

        result = await _query_codex(mock_ctx, "test prompt", model="gpt-4")

        mock_generate.assert_awaited_once()
        assert result == "api response"


class TestCodeGenerate:
    """Tests for the code_generate tool."""

    @pytest.mark.asyncio
    @patch(
        "codexmcp.tools.prompts.get",
        lambda *args, **kwargs: "Example prompt {description}",
    )
    @patch("codexmcp.tools._query_codex")
    async def test_code_generate(self, mock_query_codex):
        """Test code_generate with default parameters."""
        # Setup
        mock_query_codex.return_value = "def example(): pass"
        mock_ctx = MagicMock(spec=Context)

        # Call the function
        result = await code_generate(mock_ctx, "Create an empty function")

        # Assertions
        assert result == "def example(): pass"
        mock_query_codex.assert_called_once()
        # Check prompt contains essential elements
        prompt = mock_query_codex.call_args[0][1]
        assert "Create an empty function" in prompt

    @pytest.mark.asyncio
    @patch(
        "codexmcp.tools.prompts.get",
        lambda *args, **kwargs: "Example prompt {description}",
    )
    @patch("codexmcp.tools._query_codex")
    async def test_code_generate_custom_language(self, mock_query_codex):
        """Test code_generate with custom language."""
        # Setup
        mock_query_codex.return_value = "function example() {}"
        mock_ctx = MagicMock(spec=Context)

        # Call the function
        result = await code_generate(mock_ctx, "Create an empty function", language="JavaScript")

        # Assertions
        assert result == "function example() {}"
        prompt = mock_query_codex.call_args[0][1]
        assert "JavaScript" in prompt


class TestReviewCode:
    """Tests for the review_code tool."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools._query_codex")
    async def test_review_code(self, mock_query_codex):
        """Test review_code function."""
        # Setup
        mock_query_codex.return_value = "Overall Quality Score: 7/10\n\nStrengths:\n..."
        mock_ctx = MagicMock(spec=Context)
        code = "def example():\n    return 42"

        # Call the function
        result = await review_code(mock_ctx, code, language="Python")

        # Assertions
        assert result == "Overall Quality Score: 7/10\n\nStrengths:\n..."
        mock_query_codex.assert_called_once()
        prompt = mock_query_codex.call_args[0][1]
        assert code in prompt
        assert "Python" in prompt


class TestDescribeCodebase:
    """Tests for the describe_codebase tool."""

    @pytest.mark.asyncio
    @patch("codexmcp.tools._query_codex")
    async def test_describe_codebase(self, mock_query_codex):
        """Test describe_codebase with basic parameters."""
        # Setup
        mock_query_codex.return_value = "This code is part of a larger system that..."
        mock_ctx = MagicMock(spec=Context)
        subject = "def process_data(data):\n    return data.transform()"

        # Call the function
        result = await describe_codebase(
            mock_ctx, subject=subject, audience="developer", detail_level="medium"
        )

        # Assertions
        assert result == "This code is part of a larger system that..."
        mock_query_codex.assert_called_once()
        prompt = mock_query_codex.call_args[0][1]
        assert subject in prompt
        assert "developer" in prompt.lower()
        assert "medium" in prompt.lower()
