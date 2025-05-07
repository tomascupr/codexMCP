"""Unit tests for codexmcp exceptions module."""

import pytest
from fastmcp import exceptions as fastmcp_exceptions

from codexmcp.exceptions import (
    CodexBaseError,
    CodexRateLimitError,
    CodexTimeoutError,
    CodexInvalidPromptError,
    CodexModelUnavailableError,
    CodexConnectionError,
)


class TestCodexBaseError:
    """Tests for the CodexBaseError class."""

    def test_init_with_message(self):
        """Test initialization with just a message."""
        error = CodexBaseError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_id is None
        assert isinstance(error, fastmcp_exceptions.ToolError)

    def test_init_with_error_id(self):
        """Test initialization with message and error_id."""
        error = CodexBaseError("Test error message", "abc123")
        assert str(error) == "Test error message (Error ID: abc123)"
        assert error.error_id == "abc123"


class TestSpecificExceptions:
    """Tests for specific exception classes."""

    def test_rate_limit_error(self):
        """Test CodexRateLimitError."""
        error = CodexRateLimitError("Rate limit exceeded", "rate123")
        assert str(error) == "Rate limit exceeded (Error ID: rate123)"
        assert error.error_id == "rate123"
        assert isinstance(error, CodexBaseError)
        assert isinstance(error, fastmcp_exceptions.ToolError)

    def test_timeout_error(self):
        """Test CodexTimeoutError."""
        error = CodexTimeoutError("Request timed out", "timeout123")
        assert str(error) == "Request timed out (Error ID: timeout123)"
        assert error.error_id == "timeout123"
        assert isinstance(error, CodexBaseError)

    def test_invalid_prompt_error(self):
        """Test CodexInvalidPromptError."""
        error = CodexInvalidPromptError("Invalid prompt parameters", "prompt123")
        assert str(error) == "Invalid prompt parameters (Error ID: prompt123)"
        assert error.error_id == "prompt123"
        assert isinstance(error, CodexBaseError)

    def test_model_unavailable_error(self):
        """Test CodexModelUnavailableError."""
        error = CodexModelUnavailableError("Model not available", "model123")
        assert str(error) == "Model not available (Error ID: model123)"
        assert error.error_id == "model123"
        assert isinstance(error, CodexBaseError)

    def test_connection_error(self):
        """Test CodexConnectionError."""
        error = CodexConnectionError("Connection failed", "conn123")
        assert str(error) == "Connection failed (Error ID: conn123)"
        assert error.error_id == "conn123"
        assert isinstance(error, CodexBaseError)
