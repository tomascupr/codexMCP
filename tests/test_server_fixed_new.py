"""Unit tests for codexmcp server module."""

import pytest
from unittest.mock import MagicMock, patch

from codexmcp.server import _ensure_event_loop_policy


class TestServer:
    """Tests for the server module."""

    @patch("codexmcp.server.os")
    def test_ensure_event_loop_policy_windows(self, mock_os):
        """Test _ensure_event_loop_policy on Windows."""
        with patch.dict("sys.modules", {"asyncio": MagicMock()}):
            import sys
            mock_asyncio = sys.modules["asyncio"]
            mock_policy = MagicMock()
            mock_asyncio.get_event_loop_policy.return_value = mock_policy
            mock_asyncio.WindowsProactorEventLoopPolicy = MagicMock()
            mock_asyncio.WindowsProactorEventLoopPolicy.return_value = MagicMock()
            
            mock_policy.__class__.__name__ = "DefaultEventLoopPolicy"
            mock_asyncio.WindowsProactorEventLoopPolicy.__name__ = "WindowsProactorEventLoopPolicy"
            
            original_isinstance = isinstance
            
            def mock_isinstance(obj, class_or_tuple):
                if obj is mock_policy and class_or_tuple is mock_asyncio.WindowsProactorEventLoopPolicy:
                    return False
                return original_isinstance(obj, class_or_tuple)
            
            with patch("builtins.isinstance", mock_isinstance):
                mock_os.name = "nt"
                
                _ensure_event_loop_policy()
                
                mock_asyncio.set_event_loop_policy.assert_called_once()

    @patch("codexmcp.server.os")
    def test_ensure_event_loop_policy_non_windows(self, mock_os):
        """Test _ensure_event_loop_policy on non-Windows platforms."""
        mock_os.name = "posix"
        
        _ensure_event_loop_policy()
