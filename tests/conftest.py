"""Test configuration and fixtures for codexmcp."""

import sys
from unittest.mock import MagicMock
import pathlib

import pytest

# Ensure package modules under 'src' are importable without installation
project_root = pathlib.Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_context():
    """Create a mock context for testing tools."""
    context = MagicMock()
    context.progress = MagicMock()
    return context


@pytest.fixture
def mock_pipe():
    """Create a mock CodexPipe."""
    pipe = MagicMock()
    pipe.send = MagicMock()
    pipe.recv = MagicMock(return_value='{"completion": "test response"}')
    return pipe


# Remove the custom event_loop fixture as it's deprecated
