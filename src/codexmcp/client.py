"""Thread-safe LLM client with caching and retry mechanisms."""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import time
from typing import Any, ClassVar, Dict, Optional

# Optionally import OpenAI - lazy loading to support fallback modes
try:
    import openai
    _OPENAI_SDK_AVAILABLE = True
except ImportError:
    _OPENAI_SDK_AVAILABLE = False

from .logging_cfg import logger


class LLMClient:
    """Thread-safe singleton LLM client with caching and retries."""
    
    _instances: ClassVar[Dict[str, "LLMClient"]] = {}
    _response_cache: Dict[str, tuple] = {}  # {prompt_hash: (response, timestamp)}
    _cache_ttl = 3600  # 1 hour cache TTL
    
    def __new__(cls, provider: str = "openai"):
        if provider not in cls._instances:
            cls._instances[provider] = super().__new__(cls)
            cls._instances[provider]._init(provider)
        return cls._instances[provider]
    
    def _init(self, provider: str):
        """Initialize the client for the specified provider."""
        self.provider = provider
        self.client = None
        if provider == "openai" and _OPENAI_SDK_AVAILABLE:
            self.client = openai.AsyncOpenAI()
            logger.info("Initialized OpenAI client")
        else:
            logger.warning(f"Provider {provider} not available or not supported")
        
    def _hash_prompt(self, prompt: str, **params) -> str:
        """Create deterministic hash for prompt+params."""
        # Sort parameters for consistent hashing
        params_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        combined = f"{prompt}:{params_str}"
        # Use SHA256 for secure, deterministic hashing
        return hashlib.sha256(combined.encode()).hexdigest()
        
    async def generate(self, prompt: str, **params) -> str:
        """Generate LLM response with caching and retries."""
        prompt_hash = self._hash_prompt(prompt, **params)
        
        # Check cache
        if prompt_hash in self._response_cache:
            response, timestamp = self._response_cache[prompt_hash]
            if time.time() - timestamp < self._cache_ttl:
                logger.info("Cache hit for prompt %s", prompt_hash[:8])
                return response
            
        # Generate with retries
        retries, max_retries = 0, 3
        while retries <= max_retries:
            try:
                if self.provider == "openai" and self.client:
                    response = await self._generate_openai(prompt, **params)
                else:
                    raise ValueError(f"Provider {self.provider} not configured")
                
                # Cache successful response
                self._response_cache[prompt_hash] = (response, time.time())
                logger.info("Generated and cached response for %s", prompt_hash[:8])
                return response
                
            except Exception as e:
                retries += 1
                logger.warning(f"Attempt {retries}/{max_retries+1} failed: {str(e)}")
                if retries > max_retries:
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise
                # Exponential backoff
                backoff_time = 2 ** retries
                logger.info(f"Backing off for {backoff_time} seconds")
                await asyncio.sleep(backoff_time)
    
    async def _generate_openai(self, prompt: str, **params) -> str:
        """Generate completion using OpenAI's API."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
            
        # Convert CodexMCP parameters to OpenAI parameters
        model = params.get("model", "gpt-4o")
        temp = params.get("temperature", 0.2)
        max_tokens = params.get("max_tokens", 4096)
        
        try:
            chat_resp = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tokens,
                stream=False,  # Maintain non-streaming for compatibility
            )
            
            # Extract and normalize response text
            return chat_resp.choices[0].message.content.lstrip("\n")
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise