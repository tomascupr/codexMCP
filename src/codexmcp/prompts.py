"""Efficient prompt template manager with versioning."""

from __future__ import annotations

import importlib.resources
from typing import Dict, Any, Optional

from .logging_cfg import logger


class PromptManager:
    """Manages prompt templates with efficient loading and formatting."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._prompts = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompts into memory once."""
        try:
            for name in importlib.resources.contents(f"{__package__}.prompts"):
                if name.endswith(".txt"):
                    prompt_name = name.replace(".txt", "")
                    try:
                        content = importlib.resources.read_text(f"{__package__}.prompts", name)
                        self._prompts[prompt_name] = content
                        logger.debug(f"Loaded prompt template: {prompt_name}")
                    except Exception as e:
                        logger.error(f"Failed to load prompt {name}: {str(e)}")
            
            logger.info(f"Loaded {len(self._prompts)} prompt templates")
        except Exception as e:
            logger.error(f"Failed to load prompts directory: {str(e)}")
    
    def get(self, name: str, **kwargs) -> str:
        """Get formatted prompt, throwing error if not found.
        
        Args:
            name: The name of the prompt template
            **kwargs: Format parameters for the template
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If prompt not found or missing format parameters
        """
        if name not in self._prompts:
            logger.error(f"Prompt template '{name}' not found")
            raise ValueError(f"Prompt template '{name}' not found")
            
        prompt_template = self._prompts[name]
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required prompt parameter: {e}")
            raise ValueError(f"Missing required prompt parameter: {e}")
            
    def exists(self, name: str) -> bool:
        """Check if prompt exists."""
        return name in self._prompts
        
    def list_prompts(self) -> list[str]:
        """Return list of available prompt names."""
        return list(self._prompts.keys())


# Global singleton instance
prompts = PromptManager()