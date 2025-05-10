"""Unit tests for codexmcp server module."""

import pytest
from unittest.mock import MagicMock, patch

from codexmcp.server import _ensure_event_loop_policy, main


class TestEventLoopPolicy:
    """Tests for event loop policy configuration."""

    @patch("os.name", "nt")
    @patch("asyncio.get_event_loop_policy")
    @patch("asyncio.set_event_loop_policy")
    def test_ensure_policy_windows(self, mock_set_policy, mock_get_policy):
        """Test event loop policy configuration on Windows."""
        import asyncio

        class DummyPolicy:
            pass

        asyncio.WindowsProactorEventLoopPolicy = DummyPolicy
        mock_get_policy.return_value = object()
        _ensure_event_loop_policy()
        mock_get_policy.assert_called_once()
        mock_set_policy.assert_called_once()
        # Verify the policy set is an instance of our DummyPolicy
        called_policy = mock_set_policy.call_args[0][0]
        assert isinstance(called_policy, DummyPolicy)

    @patch("os.name", "posix")
    @patch("asyncio.get_event_loop_policy")
    @patch("asyncio.set_event_loop_policy")
    def test_ensure_policy_posix(self, mock_set_policy, mock_get_policy):
        """Test event loop policy configuration on POSIX systems."""
        # Call function
        _ensure_event_loop_policy()

        # Assertions
        mock_get_policy.assert_not_called()
        mock_set_policy.assert_not_called()


class TestMain:
    """Tests for the main function."""

    @patch("codexmcp.server._ensure_event_loop_policy")
    @patch("codexmcp.server.logger")
    @patch("codexmcp.server.pipe", None)  # Simulate missing pipe
    def test_main_no_pipe(self, mock_logger, mock_ensure_policy):
        """Test main function with missing pipe."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        mock_logger.error.assert_called_once_with(
            "Shared CodexPipe failed to initialize. Server cannot start."
        )

    @patch(
        "codexmcp.server.pipe", MagicMock()
    )  # Mock pipe to skip initialization check
    def test_main_success(self):
        """Test main function proceeds to server run and exits on error."""
        with pytest.raises(SystemExit):
            main()

    @patch("codexmcp.server._ensure_event_loop_policy")
    @patch("codexmcp.server.logger")
    @patch("codexmcp.server.pipe", MagicMock())  # Mock pipe
    @patch("importlib.import_module")
    @patch("sys.exit")
    def test_main_import_error(
        self, mock_exit, mock_import_module, mock_logger, mock_ensure_policy
    ):
        """Test main function with import error."""
        mock_import_module.side_effect = ImportError("fail import")
        main()
        mock_exit.assert_called_once_with(1)
        mock_logger.error.assert_called_once()
