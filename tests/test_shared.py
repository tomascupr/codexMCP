"""Unit tests for codexmcp shared module."""

import os
import pytest
from unittest.mock import patch

from codexmcp.shared import __version__


class TestSharedModule:
    """Tests for the shared module."""

    def test_version_exists(self):
        """Test that version is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        # Version should follow semantic versioning (at least 2 dots)
        assert __version__.count(".") >= 2

    def test_version_format(self):
        """Test that version follows semantic versioning."""
        parts = __version__.split(".")
        assert len(parts) >= 3
        # All parts should be numeric
        for part in parts:
            assert part.isdigit()

    @pytest.mark.skip(
        reason="This test requires module reloading which affects other tests"
    )
    def test_mcp_initialization(self):
        """Test that the MCP instance is initialized."""
        with patch("codexmcp.shared.FastMCP") as mock_fastmcp:
            # We need to import here to get the patched version
            import codexmcp.shared
            from importlib import reload

            reload(codexmcp.shared)

            # Verify FastMCP was initialized with the correct name
            mock_fastmcp.assert_called_once_with("CodexMCP")
            assert codexmcp.shared.mcp is not None

    @pytest.mark.skip(
        reason="This test requires module reloading which affects other tests"
    )
    def test_pipe_initialization(self):
        """Test pipe initialization logic."""
        # This test would require complex module reloading which can affect other tests
        # For a reliable test suite, we'll skip detailed initialization tests
        # that require reloading shared module
        pass

    def test_environment_variable(self):
        """Test that CODEX_ALLOW_DIRTY is set."""
        assert os.environ.get("CODEX_ALLOW_DIRTY") is not None
