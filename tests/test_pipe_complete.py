"""Unit tests for codexmcp pipe module."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from codexmcp.pipe import CodexPipe, ANSI_RE


class TestCodexPipe:
    """Tests for the CodexPipe class."""

    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    def test_init(self, mock_thread, mock_popen):
        """Test initialization of CodexPipe."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        pipe = CodexPipe(["test", "command"])
        
        mock_popen.assert_called_once()
        assert pipe.process is not None
        assert pipe._stderr_thread is not None
        assert pipe._write_lock is not None
        
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    def test_init_error_handling(self, mock_thread, mock_popen):
        """Test error handling during initialization."""
        mock_process = MagicMock()
        mock_process.stdin = None  # This should cause an error
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        with pytest.raises(RuntimeError):
            CodexPipe(["test", "command"])

    @pytest.mark.asyncio
    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    async def test_send(self, mock_thread, mock_popen):
        """Test send method."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        pipe = CodexPipe(["test", "command"])
        
        pipe._write = MagicMock()
        
        message = {"prompt": "test", "model": "o4-mini"}
        await pipe.send(message)
        
        expected_data = json.dumps(message, ensure_ascii=False)
        pipe._write.assert_called_once_with(expected_data)

    @pytest.mark.asyncio
    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    @patch("codexmcp.pipe.asyncio.to_thread")
    @patch("codexmcp.pipe.asyncio.wait_for")
    async def test_recv_success(self, mock_wait_for, mock_to_thread, mock_thread, mock_popen):
        """Test recv method with successful response."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = '{"completion": "test response"}\n'
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        mock_to_thread.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
        
        mock_wait_for.side_effect = lambda awaitable, timeout: awaitable
        
        pipe = CodexPipe(["test", "command"])
        
        response = await pipe.recv()
        
        assert response == '{"completion": "test response"}'
        mock_process.stdout.readline.assert_called_once()

    @pytest.mark.asyncio
    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    @patch("codexmcp.pipe.asyncio.to_thread")
    @patch("codexmcp.pipe.asyncio.wait_for")
    async def test_recv_empty_response(self, mock_wait_for, mock_to_thread, mock_thread, mock_popen):
        """Test recv method with empty response (terminated subprocess)."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = ""  # Empty response
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        mock_to_thread.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
        
        mock_wait_for.side_effect = lambda awaitable, timeout: awaitable
        
        pipe = CodexPipe(["test", "command"])
        
        with pytest.raises(RuntimeError, match="Codex subprocess terminated unexpectedly"):
            await pipe.recv()

    @pytest.mark.asyncio
    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    @patch("codexmcp.pipe.asyncio.to_thread")
    @patch("codexmcp.pipe.asyncio.wait_for")
    async def test_recv_with_progress_callback(self, mock_wait_for, mock_to_thread, mock_thread, mock_popen):
        """Test recv method with progress callback."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.side_effect = ["", '{"completion": "test response"}\n']
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        mock_to_thread.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
        
        mock_wait_for.side_effect = [asyncio.TimeoutError, lambda: '{"completion": "test response"}\n']
        
        pipe = CodexPipe(["test", "command"])
        
        progress_cb = MagicMock()
        
        with pytest.raises(asyncio.TimeoutError):
            await pipe.recv(progress_cb=progress_cb, silent_timeout=1.0)
        
        progress_cb.assert_called_once_with("still working")

    def test_write(self):
        """Test _write method."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        
        pipe = CodexPipe.__new__(CodexPipe)  # Create instance without calling __init__
        pipe.process = mock_process
        
        pipe._write('{"prompt": "test"}')
        
        mock_process.stdin.write.assert_called_once_with('{"prompt": "test"}\n')
        mock_process.stdin.flush.assert_called_once()

    @patch("codexmcp.pipe.logger")
    def test_drain_stderr(self, mock_logger):
        """Test _drain_stderr method."""
        mock_process = MagicMock()
        mock_process.stderr = ["Line with \x1b[31mcolor\x1b[0m\n", "Normal line\n"]
        
        pipe = CodexPipe.__new__(CodexPipe)  # Create instance without calling __init__
        pipe.process = mock_process
        
        pipe._drain_stderr()
        
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call("stderr: %s", "Line with color")
        mock_logger.info.assert_any_call("stderr: %s", "Normal line")

    @pytest.mark.asyncio
    @patch("codexmcp.pipe.Popen")
    @patch("codexmcp.pipe.threading.Thread")
    @patch("codexmcp.pipe.asyncio.to_thread")
    async def test_aclose(self, mock_to_thread, mock_thread, mock_popen):
        """Test aclose method."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.poll.return_value = None  # Process is still running
        mock_popen.return_value = mock_process
        
        mock_to_thread.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
        
        pipe = CodexPipe(["test", "command"])
        
        await pipe.aclose()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)

    def test_ansi_regex(self):
        """Test the ANSI regex pattern."""
        colored_text = "\x1b[31mError\x1b[0m: Something went wrong"
        clean_text = ANSI_RE.sub("", colored_text)
        assert clean_text == "Error: Something went wrong"
        
        complex_text = "\x1b[1;32mSuccess\x1b[0m\x1b[K: Task completed"
        clean_complex = ANSI_RE.sub("", complex_text)
        assert clean_complex == "Success: Task completed"
