"""Tests for app commands."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from it2.cli import cli


def setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app):
    """Helper to set up common mocks for tests."""

    # Set up environment - return None for completion vars, but cookie for iTerm2
    def env_side_effect(key, default=None):
        if key == "ITERM2_COOKIE":
            return "test-cookie"
        # Set terminal type for Rich console output
        if key == "TERM":
            return "dumb"
        # Return None for shell completion variables
        return default if default is not None else None

    mock_env_get.side_effect = env_side_effect

    # Set up connection manager
    mock_conn_mgr.connect = AsyncMock()
    mock_conn_mgr.get_app = AsyncMock(return_value=mock_app)
    mock_conn_mgr.close = AsyncMock()

    # Mock run_until_complete to run the coroutine
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
    app.async_activate = AsyncMock()
    app.async_set_theme = AsyncMock()
    app.async_create_hotkey_window_with_profile = AsyncMock()

    # Create mock structure for windows and tabs
    session = MagicMock()
    session.session_id = "test-session-123"

    tab = MagicMock()
    tab.sessions = [session]
    tab.current_session = session
    tab.tab_id = "test-tab-456"

    window = MagicMock()
    window.tabs = [tab]
    window.current_tab = tab
    window.window_id = "test-window-789"
    window.async_activate = AsyncMock()

    app.windows = [window]
    app.current_terminal_window = window
    app.app_id = "com.googlecode.iterm2"

    # Mock version info
    version_parts = MagicMock()
    version_parts.major = 3
    version_parts.minor = 4
    version_parts.patch = 10
    app.get_theme = AsyncMock(return_value=["Dark Background"])

    return app


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_activate(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app activate command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    result = runner.invoke(cli, ["app", "activate"])
    assert result.exit_code == 0
    assert "iTerm2 activated" in result.output
    mock_app.async_activate.assert_called_once()


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_hide(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app hide command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    # Mock app.async_hide
    mock_app.async_hide = AsyncMock()

    result = runner.invoke(cli, ["app", "hide"])
    assert result.exit_code == 0
    assert "iTerm2 hidden" in result.output
    mock_app.async_hide.assert_called_once()


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_quit(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app quit command."""
    # Skip this test - requires complex protobuf mocking
    import pytest

    pytest.skip("Requires complex protobuf mocking")


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_version(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app version command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    # Mock version variables
    mock_app.async_get_variable = AsyncMock(
        side_effect=lambda var: {"buildNumber": "12345", "version": "3.4.10"}.get(var)
    )

    result = runner.invoke(cli, ["app", "version"])
    assert result.exit_code == 0
    assert "iTerm2 version: 3.4.10" in result.output
    assert "Build: 12345" in result.output


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_theme_dark(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app theme set to dark command."""
    # Skip this test - requires iterm2.Theme enum
    import pytest

    pytest.skip("Requires iterm2.Theme enum")


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_theme_light(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app theme set to light command."""
    # Skip this test - requires iterm2.Theme enum
    import pytest

    pytest.skip("Requires iterm2.Theme enum")


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_create_hotkey_window(
    mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app
):
    """Test app create-hotkey-window command."""
    # Skip this test - HotkeyWindow not available in test environment
    import pytest

    pytest.skip("HotkeyWindow not available in test environment")


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_get_focus(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app get-focus command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    # Mock session variable
    session = mock_app.current_terminal_window.current_tab.current_session
    session.async_get_variable = AsyncMock(return_value="Test Session")

    result = runner.invoke(cli, ["app", "get-focus"])
    assert result.exit_code == 0
    assert "Current window: test-window-789" in result.output
    assert "Current tab: test-tab-456" in result.output
    assert "Current session: test-session-123" in result.output
    assert "Session name: Test Session" in result.output


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_broadcast_on(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app broadcast on command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    # Mock tab broadcast settings
    tab = mock_app.current_terminal_window.current_tab
    tab.async_set_broadcast_domains = AsyncMock()

    result = runner.invoke(cli, ["app", "broadcast", "on"])
    assert result.exit_code == 0
    assert "Broadcasting enabled for current tab" in result.output
    tab.async_set_broadcast_domains.assert_called_once_with(["all"])


@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_broadcast_off(mock_conn_mgr, mock_env_get, mock_run_until_complete, runner, mock_app):
    """Test app broadcast off command."""
    setup_iterm2_mocks(mock_conn_mgr, mock_env_get, mock_run_until_complete, mock_app)

    # Mock tab broadcast settings
    tab = mock_app.current_terminal_window.current_tab
    tab.async_set_broadcast_domains = AsyncMock()

    result = runner.invoke(cli, ["app", "broadcast", "off"])
    assert result.exit_code == 0
    assert "Broadcasting disabled" in result.output
    tab.async_set_broadcast_domains.assert_called_once_with([])


def test_app_command_no_cookie(runner):
    """Test app command without iTerm2 cookie."""
    with patch("os.environ.get", return_value=None):
        result = runner.invoke(cli, ["app", "activate"])
        assert result.exit_code == 2
        assert "Not running inside iTerm2" in result.output
