"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from it2.utils.config import Config


@pytest.fixture()
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "profiles": {
                "test-profile": [
                    {"command": "cd /tmp"},
                    {"split": "vertical"},
                    {"pane1": "ls -la"},
                    {"pane2": "pwd"},
                ]
            },
            "aliases": {
                "test-alias": 'session send "test"',
                "test-run": 'session run "echo hello"',
            },
        }
        yaml.dump(config_data, f)
        config_path = f.name

    yield config_path

    # Cleanup
    os.unlink(config_path)


def test_config_load(temp_config_file):
    """Test loading configuration from file."""
    # Set environment variable to point to temp file
    os.environ["IT2_CONFIG_PATH"] = temp_config_file

    try:
        config = Config()

        # Test profile loading
        profile = config.get_profile("test-profile")
        assert profile is not None
        assert len(profile) == 4
        assert profile[0]["command"] == "cd /tmp"
        assert profile[1]["split"] == "vertical"

        # Test alias loading
        alias = config.get_alias("test-alias")
        assert alias == 'session send "test"'

        # Test non-existent items
        assert config.get_profile("non-existent") is None
        assert config.get_alias("non-existent") is None

        # Test get all
        all_profiles = config.get_all_profiles()
        assert len(all_profiles) == 1
        assert "test-profile" in all_profiles

        all_aliases = config.get_all_aliases()
        assert len(all_aliases) == 2
        assert "test-alias" in all_aliases
        assert "test-run" in all_aliases
    finally:
        del os.environ["IT2_CONFIG_PATH"]


def test_config_missing_file():
    """Test behavior when config file doesn't exist."""
    # Use a non-existent path
    import tempfile

    temp_dir = tempfile.mkdtemp()
    non_existent_path = os.path.join(temp_dir, "non-existent-config.yaml")
    os.environ["IT2_CONFIG_PATH"] = non_existent_path

    try:
        config = Config()

        # Should return empty results
        assert config.get_profile("any") is None
        assert config.get_alias("any") is None
        assert config.get_all_profiles() == {}
        assert config.get_all_aliases() == {}
    finally:
        del os.environ["IT2_CONFIG_PATH"]
        os.rmdir(temp_dir)


def test_config_invalid_yaml():
    """Test behavior with invalid YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: ][")
        config_path = f.name

    os.environ["IT2_CONFIG_PATH"] = config_path

    try:
        config = Config()

        # Should handle gracefully and return empty config
        assert config.config == {}
    finally:
        del os.environ["IT2_CONFIG_PATH"]
        os.unlink(config_path)


def test_config_default_path():
    """Test default config path resolution."""
    # Don't set environment variable
    if "IT2_CONFIG_PATH" in os.environ:
        del os.environ["IT2_CONFIG_PATH"]

    config = Config()

    # Should use ~/.it2rc.yaml
    assert config.config_path == Path.home() / ".it2rc.yaml"
