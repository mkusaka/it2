"""Tests for profile commands."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from it2.cli import cli


def setup_iterm2_mocks(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_app,
):
    """Helper to set up common mocks for tests."""

    def env_side_effect(key, default=None):
        if key == "ITERM2_COOKIE":
            return "test-cookie"
        if key == "TERM":
            return "dumb"
        return default if default is not None else None

    mock_env_get.side_effect = env_side_effect

    mock_connection = MagicMock()
    mock_async_create.return_value = mock_connection
    mock_async_get_app.return_value = mock_app

    mock_conn_mgr.connect = AsyncMock()
    mock_conn_mgr.get_app = AsyncMock(return_value=mock_app)
    mock_conn_mgr.close = AsyncMock()

    def run_coro(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    mock_run_until_complete.side_effect = run_coro


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_app():
    """Create a mock app."""
    app = MagicMock()

    session = MagicMock()
    session.session_id = "test-session-123"
    session.async_set_profile = AsyncMock()

    tab = MagicMock()
    tab.sessions = [session]
    tab.current_session = session

    window = MagicMock()
    window.tabs = [tab]
    window.current_tab = tab

    app.windows = [window]
    app.current_terminal_window = window
    app.get_session_by_id = MagicMock(return_value=session)

    return app


@patch("iterm2.PartialProfile.async_query")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_profile_list(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_query,
    runner,
    mock_app,
):
    """Test profile list command with JSON output."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    profile1 = MagicMock()
    profile1.guid = "guid-1"
    profile1.name = "Default"
    profile2 = MagicMock()
    profile2.guid = "guid-2"
    profile2.name = "Custom"
    mock_query.return_value = [profile1, profile2]

    result = runner.invoke(cli, ["profile", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "Default"
    assert data[1]["name"] == "Custom"


@patch("iterm2.PartialProfile.async_query")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_profile_show(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_query,
    runner,
    mock_app,
):
    """Test profile show command parses normal_font string correctly."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # normal_font returns a string like "Monaco 12"
    full_profile = MagicMock()
    full_profile.guid = "guid-1"
    full_profile.name = "Default"
    full_profile.normal_font = "Monaco 12"
    full_profile.background_color = MagicMock(__str__=lambda s: "#000000")
    full_profile.foreground_color = MagicMock(__str__=lambda s: "#ffffff")
    full_profile.transparency = 0.0
    full_profile.blur = False
    full_profile.cursor_color = MagicMock(__str__=lambda s: "#00ff00")
    full_profile.selection_color = MagicMock(__str__=lambda s: "#0000ff")
    full_profile.badge_text = ""

    partial_profile = MagicMock()
    partial_profile.name = "Default"
    partial_profile.async_get_full_profile = AsyncMock(return_value=full_profile)
    mock_query.return_value = [partial_profile]

    result = runner.invoke(cli, ["profile", "show", "Default", "--json"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    data = json.loads(result.output)
    assert data["name"] == "Default"
    # normal_font is a str; font_size should be parsed from it
    assert data["font_size"] == 12.0
    assert data["font"] == "Monaco 12"


@patch("iterm2.PartialProfile.async_query")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_profile_set_font_size(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_query,
    runner,
    mock_app,
):
    """Test profile set font-size uses async_set_normal_font."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    full_profile = MagicMock()
    full_profile.normal_font = "Monaco 12"
    full_profile.async_set_normal_font = AsyncMock()

    partial_profile = MagicMock()
    partial_profile.name = "Default"
    partial_profile.async_get_full_profile = AsyncMock(return_value=full_profile)
    mock_query.return_value = [partial_profile]

    result = runner.invoke(cli, ["profile", "set", "Default", "font-size", "14"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Set font-size = 14" in result.output
    full_profile.async_set_normal_font.assert_called_once_with("Monaco 14")


@patch("iterm2.PartialProfile.async_query")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_profile_set_bg_color(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_query,
    runner,
    mock_app,
):
    """Test profile set bg-color uses async_set_background_color with int Color."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    full_profile = MagicMock()
    full_profile.normal_font = "Monaco 12"
    full_profile.async_set_background_color = AsyncMock()

    partial_profile = MagicMock()
    partial_profile.name = "Default"
    partial_profile.async_get_full_profile = AsyncMock(return_value=full_profile)
    mock_query.return_value = [partial_profile]

    result = runner.invoke(cli, ["profile", "set", "Default", "bg-color", "#ff8800"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Set bg-color = #ff8800" in result.output
    full_profile.async_set_background_color.assert_called_once()


def test_profile_create_removed(runner):
    """Test that create subcommand no longer exists."""
    result = runner.invoke(cli, ["profile", "create", "NewProfile"])
    # Should fail because the command doesn't exist
    assert result.exit_code != 0
    assert "No such command" in result.output or "Usage:" in result.output
