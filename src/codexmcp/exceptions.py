"""Custom exception classes for CodexMCP."""

from __future__ import annotations

from fastmcp import exceptions


class CodexBaseError(exceptions.ToolError):
    """Base exception class for CodexMCP errors."""

    def __init__(self, message: str, error_id: str = None):
        self.error_id = error_id
        message_with_id = f"{message} (Error ID: {error_id})" if error_id else message
        super().__init__(message_with_id)


class CodexRateLimitError(CodexBaseError):
    """Raised when rate limits are exceeded."""

    pass


class CodexTimeoutError(CodexBaseError):
    """Raised when a request times out."""

    pass


class CodexInvalidPromptError(CodexBaseError):
    """Raised when a prompt has invalid parameters."""

    pass


class CodexModelUnavailableError(CodexBaseError):
    """Raised when the requested model is unavailable."""

    pass


class CodexConnectionError(CodexBaseError):
    """Raised when there's a connection issue with the LLM provider."""

    pass
