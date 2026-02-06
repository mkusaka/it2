"""Configuration file support for iTerm2 CLI."""

import os
from pathlib import Path
from typing import Any, Optional

import click
import yaml


class Config:
    """Configuration manager for iTerm2 CLI."""

    def __init__(self) -> None:
        self.config_path = self._get_config_path()
        self.config: dict[str, Any] = {}
        self.load()

    def _get_config_path(self) -> Path:
        """Get configuration file path."""
        # Check environment variable first
        env_path = os.environ.get("IT2_CONFIG_PATH")
        if env_path:
            return Path(env_path)

        # Default to ~/.it2rc.yaml
        return Path.home() / ".it2rc.yaml"

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self.config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                click.echo(f"Warning: Failed to parse config file: {e}", err=True)
                self.config = {}
        else:
            self.config = {}

    def get_profile(self, name: str) -> Optional[list[dict[str, Any]]]:
        """Get a custom profile by name."""
        profiles = self.config.get("profiles", {})
        result = profiles.get(name)
        return result if isinstance(result, list) else None

    def get_alias(self, name: str) -> Optional[str]:
        """Get an alias command by name."""
        aliases = self.config.get("aliases", {})
        result = aliases.get(name)
        return result if isinstance(result, str) else None

    def get_all_profiles(self) -> dict[str, list[dict[str, Any]]]:
        """Get all custom profiles."""
        result = self.config.get("profiles", {})
        return result if isinstance(result, dict) else {}

    def get_all_aliases(self) -> dict[str, str]:
        """Get all aliases."""
        result = self.config.get("aliases", {})
        return result if isinstance(result, dict) else {}
