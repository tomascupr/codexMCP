"""Configuration management for CodexMCP."""

from __future__ import annotations

import os

from .logging_cfg import logger


class Config:
    """Configuration singleton with environment variable support."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Initialize configuration from environment variables."""
        # Cache settings
        self.cache_enabled = os.environ.get("CODEXMCP_CACHE_ENABLED", "1").lower() in (
            "1",
            "true",
            "yes",
        )
        self.cache_ttl = int(os.environ.get("CODEXMCP_CACHE_TTL", "3600"))

        # Retry settings
        self.max_retries = int(os.environ.get("CODEXMCP_MAX_RETRIES", "3"))
        self.retry_backoff = float(os.environ.get("CODEXMCP_RETRY_BACKOFF", "2.0"))

        # Model settings
        self.default_model = os.environ.get("CODEXMCP_DEFAULT_MODEL", "o4-mini")
        self.default_temperature = float(os.environ.get("CODEXMCP_DEFAULT_TEMP", "0.2"))
        self.default_max_tokens = int(
            os.environ.get("CODEXMCP_DEFAULT_MAX_TOKENS", "4096")
        )

        # Log configuration values
        self._log_config()

    def _log_config(self):
        """Log the current configuration."""
        logger.info("CodexMCP Configuration:")
        logger.info(
            f"  Cache: {'enabled' if self.cache_enabled else 'disabled'} (TTL: {self.cache_ttl}s)"
        )
        logger.info(f"  Retries: max={self.max_retries}, backoff={self.retry_backoff}")
        logger.info(f"  Default model: {self.default_model}")
        logger.info(
            f"  Default params: temp={self.default_temperature}, max_tokens={self.default_max_tokens}"
        )


# Global singleton instance
config = Config()
