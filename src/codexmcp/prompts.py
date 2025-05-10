"""Efficient prompt template manager with versioning."""

from __future__ import annotations

import importlib.resources
from typing import Dict

from .logging_cfg import logger


class PromptManager:
    """Manages prompt templates with efficient loading and formatting."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Call _init only if it hasn't been called before for the instance
            if (
                not hasattr(cls._instance, "_initialized")
                or not cls._instance._initialized
            ):
                cls._instance._init()
        return cls._instance

    def _init(self):
        logger.debug("PromptManager _init called.")
        self._prompts: Dict[str, str] = {}
        self._loaded: bool = False  # Flag to track if prompts have been loaded
        self._initialized: bool = True
        # self._load_prompts() # Don't load immediately

    def ensure_loaded(self):
        """Ensure that prompts are loaded if they haven't been already."""
        if not self._loaded:
            logger.debug(
                "PromptManager: Prompts not loaded yet. Calling _load_prompts."
            )
            self._load_prompts()
        else:
            logger.debug("PromptManager: Prompts already loaded.")

    def _load_prompts(self):
        """Load all prompts into memory. Sets _loaded to True upon completion."""
        if self._loaded:
            logger.debug("PromptManager _load_prompts: Already loaded, skipping.")
            return

        logger.info("PromptManager: Starting to load prompt templates...")
        try:
            # Determine the correct package path for resources
            # Assuming this file (prompts.py) is in 'codexmcp' package,
            # and templates are in a 'prompts' subdirectory of 'codexmcp'.
            # So, the resource path is 'codexmcp.prompts'
            resource_package = f"{__package__}.prompt_files"

            prompt_files_found = 0
            for name in importlib.resources.contents(resource_package):
                if name.endswith(".txt"):
                    prompt_name = name.replace(".txt", "")
                    try:
                        content = importlib.resources.read_text(resource_package, name)
                        self._prompts[prompt_name] = content
                        prompt_files_found += 1
                        logger.debug(f"Loaded prompt template: {prompt_name}")
                    except Exception as e:
                        logger.error(
                            f"Failed to load prompt {name} from {resource_package}: {str(e)}",
                            exc_info=True,
                        )

            self._loaded = True  # Set loaded to true AFTER attempting to load
            logger.info(
                f"PromptManager: Finished loading. {prompt_files_found} prompt templates loaded from {resource_package}."
            )
            if not self._prompts:
                logger.warning(
                    f"PromptManager: No prompts were loaded from {resource_package}. Check directory and files."
                )

        except FileNotFoundError:
            logger.error(
                f"PromptManager: Prompt directory/package '{resource_package}' not found. Cannot load prompts.",
                exc_info=True,
            )
            self._loaded = True  # Still set to true to prevent reload attempts for a non-existent path
        except Exception as e:
            logger.error(
                f"PromptManager: Failed to load prompts directory '{resource_package}': {str(e)}",
                exc_info=True,
            )
            self._loaded = True  # Avoid repeated failures

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
        self.ensure_loaded()
        if name not in self._prompts:
            logger.error(
                f"Prompt template '{name}' not found after ensuring loaded. Available: {list(self._prompts.keys())}"
            )
            raise ValueError(f"Prompt template '{name}' not found")

        prompt_template = self._prompts[name]
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required prompt parameter for '{name}': {e}")
            raise ValueError(f"Missing required prompt parameter for '{name}': {e}")

    def exists(self, name: str) -> bool:
        """Check if prompt exists."""
        self.ensure_loaded()
        return name in self._prompts

    def list_prompts(self) -> list[str]:
        """Return list of available prompt names."""
        self.ensure_loaded()
        return list(self._prompts.keys())


# Global singleton instance
prompts = PromptManager()
