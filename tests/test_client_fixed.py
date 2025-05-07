"""Unit tests for codexmcp client module with proper mocking."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from codexmcp.client import LLMClient


class TestLLMClient:
    """Tests for the LLMClient class."""

    def test_singleton_pattern(self):
        """Test that LLMClient follows the singleton pattern."""
        client1 = LLMClient()
        client2 = LLMClient()
        assert client1 is client2
        
        with patch("codexmcp.client._OPENAI_SDK_AVAILABLE", True):
            client3 = LLMClient("anthropic")  # Different provider
            assert client1 is not client3
            
            client4 = LLMClient("anthropic")
            assert client3 is client4

    def test_hash_prompt(self):
        """Test the _hash_prompt method."""
        client = LLMClient()
        
        hash1 = client._hash_prompt("test prompt", model="gpt-4", temperature=0.7)
        hash2 = client._hash_prompt("test prompt", model="gpt-4", temperature=0.7)
        assert hash1 == hash2
        
        hash3 = client._hash_prompt("different prompt", model="gpt-4", temperature=0.7)
        assert hash1 != hash3
        
        hash4 = client._hash_prompt("test prompt", model="gpt-3.5", temperature=0.7)
        assert hash1 != hash4
        
        hash5 = client._hash_prompt("test prompt", temperature=0.7, model="gpt-4")
        assert hash1 == hash5

    @pytest.mark.asyncio
    async def test_generate_cache_hit(self):
        """Test generate method with cache hit."""
        client = LLMClient()
        
        prompt = "test prompt"
        params = {"model": "gpt-4", "temperature": 0.7}
        prompt_hash = client._hash_prompt(prompt, **params)
        
        async with client._cache_lock:
            client._response_cache[prompt_hash] = ("cached response", time.time())
        
        with patch.object(client, '_generate_openai', new_callable=AsyncMock) as mock_generate_openai:
            result = await client.generate(prompt, **params)
        
        assert result == "cached response"
        mock_generate_openai.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_cache_miss(self):
        """Test generate method with cache miss."""
        client = LLMClient()
        
        prompt = "new prompt"
        params = {"model": "gpt-4", "temperature": 0.7}
        
        async with client._cache_lock:
            client._response_cache.clear()
        
        with patch.object(client, 'client', create=True) as mock_client:
            with patch.object(client, '_generate_openai', new_callable=AsyncMock) as mock_generate_openai:
                mock_generate_openai.return_value = "new response"
                result = await client.generate(prompt, **params)
        
        assert result == "new response"
        mock_generate_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_cache_expired(self):
        """Test generate method with expired cache entry."""
        client = LLMClient()
        
        prompt = "test prompt"
        params = {"model": "gpt-4", "temperature": 0.7}
        prompt_hash = client._hash_prompt(prompt, **params)
        
        expired_time = time.time() - client._cache_ttl - 10
        
        async with client._cache_lock:
            client._response_cache[prompt_hash] = ("old response", expired_time)
        
        with patch.object(client, 'client', create=True) as mock_client:
            with patch.object(client, '_generate_openai', new_callable=AsyncMock) as mock_generate_openai:
                mock_generate_openai.return_value = "new response"
                result = await client.generate(prompt, **params)
        
        assert result == "new response"
        mock_generate_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_openai(self):
        """Test _generate_openai method."""
        mock_message = MagicMock()
        mock_message.content = "AI response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        client = LLMClient()
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat = MagicMock()
        mock_openai_client.chat.completions = MagicMock()
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(client, 'client', mock_openai_client):
            result = await client._generate_openai(
                "test prompt", 
                model="gpt-4", 
                temperature=0.7, 
                max_tokens=100
            )
        
        assert result == "AI response"
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "test prompt"}],
            temperature=0.7,
            max_tokens=100,
            stream=False
        )
