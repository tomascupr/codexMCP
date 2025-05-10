"""Unit tests for codexmcp pipe module (DEPRECATED).

This test module was for the now-removed pipe.py module. 
All these tests are skipped as the CodexPipe class has been replaced with cli_backend.py.
"""

import pytest


@pytest.mark.skip(reason="CodexPipe has been removed in favor of cli_backend.py")
class TestCodexPipe:
    """Tests for the deprecated CodexPipe class."""
    
    def test_skipped(self):
        """Placeholder test to indicate pipe.py has been removed."""
        pytest.skip("CodexPipe has been replaced with cli_backend in version 0.1.6")
