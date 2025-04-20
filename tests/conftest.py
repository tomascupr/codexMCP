"""Test configuration and fixtures for codexmcp."""

import os
import sys
from unittest.mock import MagicMock

import pytest


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