"""Tests for the OpenAI-SDK fallback path in `_query_codex`."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_openai_fallback_when_cli_unavailable():
    """Ensure that when Codex CLI is absent the OpenAI ChatCompletion path is used."""
    
    # Import inside the test so patches are applied correctly
    with patch("codexmcp.cli_backend.is_cli_available", return_value=False):
        with patch("codexmcp.tools._OPENAI_SDK_AVAILABLE", True):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
                # Mock the OpenAI client
                mock_client = MagicMock()
                mock_stream = AsyncMock()
                
                # Create async generator for streaming
                async def mock_stream_generator():
                    chunk = SimpleNamespace(
                        choices=[SimpleNamespace(
                            delta=SimpleNamespace(content="Hello from API")
                        )]
                    )
                    yield chunk
                
                mock_stream.__aiter__ = mock_stream_generator
                mock_client.client.chat.completions.create.return_value = mock_stream
                
                with patch("codexmcp.tools.client", mock_client):
                    from codexmcp.tools import _query_codex
                    
                    # Create a minimal context with progress stub
                    class MockContext:
                        async def progress(self, *args, **kwargs):
                            pass
                    
                    # Execute
                    result = await _query_codex(MockContext(), "test prompt", model="gpt-4o-mini")
                    
                    # Assertions
                    assert "Hello from API" in result
                    mock_client.client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_cli_backend_runtime_detection():
    """Test that CLI backend detection happens at runtime, not import time."""
    
    # This import should not fail even if CLI is not available
    from codexmcp import cli_backend
    
    # Test the availability check
    with patch("codexmcp.cli_backend.shutil.which", return_value=None):
        with patch.dict("os.environ", {}, clear=True):
            # Reset the cached state
            cli_backend._CLI_CHECKED = False
            cli_backend._CODEX_PATH_CACHE = None
            
            # Check should return False without raising
            assert cli_backend.is_cli_available() is False
            
            # Attempting to run should raise at runtime
            with pytest.raises(cli_backend.CodexCLIError) as exc_info:
                await cli_backend.run("test prompt")
            
            assert "Codex CLI binary not found" in str(exc_info.value)
            assert "fall back to OpenAI API" in str(exc_info.value)


@pytest.mark.asyncio 
async def test_cli_fallback_to_api():
    """Test that tools properly fall back from CLI to API when CLI fails."""
    
    with patch("codexmcp.cli_backend.run", side_effect=Exception("CLI failed")):
        with patch("codexmcp.tools._OPENAI_SDK_AVAILABLE", True):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
                # Mock successful API response
                with patch("codexmcp.tools._query_openai_stream", new_callable=AsyncMock) as mock_api:
                    mock_api.return_value = "API fallback response"
                    
                    from codexmcp.tools import _query_codex
                    
                    class MockContext:
                        async def progress(self, *args, **kwargs):
                            pass
                    
                    result = await _query_codex(MockContext(), "test prompt", model="gpt-4")
                    
                    assert result == "API fallback response"
                    mock_api.assert_called_once()
