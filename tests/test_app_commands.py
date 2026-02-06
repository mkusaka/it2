"""Tests for app commands."""

import asyncio
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

    # Mock the new external connection path
    mock_connection = MagicMock()
    mock_async_create.return_value = mock_connection
    mock_async_get_app.return_value = mock_app

    # Set up connection manager (legacy)
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
    app.async_get_theme = AsyncMock(return_value=["dark"])

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
    app.get_session_by_id = MagicMock(return_value=session)

    return app


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_activate(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test app activate command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["app", "activate"])
    assert result.exit_code == 0
    assert "iTerm2 activated" in result.output
    mock_app.async_activate.assert_called_once()


@patch("iterm2.MainMenu.async_select_menu_item", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_hide(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_select_menu,
    runner,
    mock_app,
):
    """Test app hide command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["app", "hide"])
    assert result.exit_code == 0
    assert "iTerm2 hidden" in result.output
    mock_select_menu.assert_called_once()


@patch("iterm2.MainMenu.async_select_menu_item", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_quit(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_select_menu,
    runner,
    mock_app,
):
    """Test app quit command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["app", "quit", "--force"])
    assert result.exit_code == 0
    assert "iTerm2 quit command sent" in result.output
    mock_select_menu.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_theme(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test app theme command shows current theme."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_app.async_get_theme = AsyncMock(return_value=["dark"])

    result = runner.invoke(cli, ["app", "theme"])
    assert result.exit_code == 0
    assert "dark" in result.output
    mock_app.async_get_theme.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_get_focus(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test app get-focus command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Mock session variable
    session = mock_app.current_terminal_window.current_tab.current_session
    session.async_get_variable = AsyncMock(return_value="Test Session")

    result = runner.invoke(cli, ["app", "get-focus"])
    assert result.exit_code == 0
    assert "Current window: test-window-789" in result.output
    assert "Current tab: test-tab-456" in result.output
    assert "Current session: test-session-123" in result.output
    assert "Session name: Test Session" in result.output


@patch("iterm2.async_set_broadcast_domains", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_broadcast_on(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_set_broadcast,
    runner,
    mock_app,
):
    """Test app broadcast on command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["app", "broadcast", "on"])
    assert result.exit_code == 0
    assert "Broadcasting enabled for current tab" in result.output
    mock_set_broadcast.assert_called_once()


@patch("iterm2.async_set_broadcast_domains", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_app_broadcast_off(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_set_broadcast,
    runner,
    mock_app,
):
    """Test app broadcast off command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["app", "broadcast", "off"])
    assert result.exit_code == 0
    assert "Broadcasting disabled" in result.output
    mock_set_broadcast.assert_called_once()


def test_app_command_no_cookie(runner):
    """Test app command without iTerm2 cookie."""
    with patch("os.environ.get", return_value=None), patch(
        "iterm2.Connection.async_create", side_effect=Exception("Connection failed")
    ):
        result = runner.invoke(cli, ["app", "activate"])
        assert result.exit_code == 2
        assert "Not running inside iTerm2" in result.output
