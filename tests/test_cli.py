"""Tests for CLI commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from it2.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "iTerm2 CLI - Control iTerm2 from the command line" in result.output
    assert "Commands:" in result.output


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "it2, version" in result.output


def test_cli_no_command(runner):
    """Test CLI with no command shows help."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "iTerm2 CLI - Control iTerm2 from the command line" in result.output


def test_session_help(runner):
    """Test session command help."""
    result = runner.invoke(cli, ["session", "--help"])
    assert result.exit_code == 0
    assert "Manage iTerm2 sessions" in result.output
    assert "Commands:" in result.output
    assert "send" in result.output
    assert "run" in result.output
    assert "split" in result.output


def test_shortcuts(runner):
    """Test that shortcuts are registered."""
    # Test send shortcut
    result = runner.invoke(cli, ["send", "--help"])
    assert result.exit_code == 0
    assert "Shortcut for 'it2 session send'" in result.output

    # Test run shortcut
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "Shortcut for 'it2 session run'" in result.output

    # Test split shortcut
    result = runner.invoke(cli, ["split", "--help"])
    assert result.exit_code == 0
    assert "Shortcut for 'it2 session split'" in result.output


def test_config_commands(runner):
    """Test config-related commands."""
    # Test config-path command
    result = runner.invoke(cli, ["config-path"])
    assert result.exit_code == 0
    assert "Configuration file:" in result.output

    # Test config-reload command
    with patch("it2.utils.config.Config.load"):
        result = runner.invoke(cli, ["config-reload"])
        assert result.exit_code == 0
        assert "Configuration reloaded" in result.output


@patch("os.environ.get")
def test_no_iterm2_cookie(mock_env_get, runner):
    """Test error when ITERM2_COOKIE is not set."""
    mock_env_get.return_value = None

    # Any command that requires connection should fail
    result = runner.invoke(cli, ["session", "list"])
    assert result.exit_code == 2
    assert "Not running inside iTerm2" in result.output


def test_command_groups_exist(runner):
    """Test that all command groups are properly registered."""
    command_groups = ["session", "window", "tab", "profile", "app", "monitor"]

    for group in command_groups:
        result = runner.invoke(cli, [group, "--help"])
        assert result.exit_code == 0
        assert "Commands:" in result.output
