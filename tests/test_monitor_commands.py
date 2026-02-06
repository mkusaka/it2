"""Tests for monitor commands."""

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
def mock_session():
    """Create a mock session."""
    session = MagicMock()
    session.session_id = "test-session-123"
    session.async_get_variable = AsyncMock()
    session.async_get_screen_contents = AsyncMock()
    return session


@pytest.fixture
def mock_app(mock_session):
    """Create a mock app."""
    app = MagicMock()

    tab = MagicMock()
    tab.sessions = [mock_session]
    tab.current_session = mock_session

    window = MagicMock()
    window.tabs = [tab]
    window.current_tab = tab

    app.windows = [window]
    app.current_terminal_window = window

    return app


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_monitor_output_no_follow(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test monitor output without follow uses line(i).string."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Mock screen contents with correct v2.13 API
    line0 = MagicMock()
    line0.string = "Hello from terminal"
    contents = MagicMock()
    contents.number_of_lines = 1
    contents.line = MagicMock(side_effect=lambda i: line0)
    mock_session.async_get_screen_contents = AsyncMock(return_value=contents)

    result = runner.invoke(cli, ["monitor", "output"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Hello from terminal" in result.output


@patch("iterm2.VariableMonitor")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_monitor_variable_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_var_monitor_cls,
    runner,
    mock_app,
    mock_session,
):
    """Test monitor variable uses VariableMonitor with 4 args."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_get_variable = AsyncMock(return_value="initial")

    # Make the context manager return values then raise KeyboardInterrupt
    mock_mon = AsyncMock()
    mock_mon.async_get = AsyncMock(side_effect=KeyboardInterrupt)
    mock_mon.__aenter__ = AsyncMock(return_value=mock_mon)
    mock_mon.__aexit__ = AsyncMock(return_value=False)
    mock_var_monitor_cls.return_value = mock_mon

    result = runner.invoke(cli, ["monitor", "variable", "jobName"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Current value: initial" in result.output

    # VariableMonitor should be called with 4 args:
    # (connection, VariableScopes.SESSION, name, session_id)
    call_args = mock_var_monitor_cls.call_args
    assert (
        len(call_args[0]) == 4 or len(call_args.args) == 4
    ), f"Expected 4 positional args to VariableMonitor, got: {call_args}"


@patch("iterm2.KeystrokeMonitor")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_monitor_keystroke(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_keystroke_monitor_cls,
    runner,
    mock_app,
    mock_session,
):
    """Test monitor keystroke uses KeystrokeMonitor with session filter."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Create a mock keystroke with .characters property
    mock_keystroke = MagicMock()
    mock_keystroke.characters = "a"

    # First call returns keystroke, second raises KeyboardInterrupt
    mock_mon = AsyncMock()
    mock_mon.async_get = AsyncMock(side_effect=[mock_keystroke, KeyboardInterrupt])
    mock_mon.__aenter__ = AsyncMock(return_value=mock_mon)
    mock_mon.__aexit__ = AsyncMock(return_value=False)
    mock_keystroke_monitor_cls.return_value = mock_mon

    result = runner.invoke(cli, ["monitor", "keystroke"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Keystroke: a" in result.output

    # KeystrokeMonitor should be called with session= kwarg
    call_kwargs = mock_keystroke_monitor_cls.call_args[1]
    assert call_kwargs.get("session") == "test-session-123"


@patch("iterm2.KeystrokeMonitor")
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_monitor_keystroke_with_pattern(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_keystroke_monitor_cls,
    runner,
    mock_app,
    mock_session,
):
    """Test monitor keystroke with regex pattern filters output."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Create mock keystrokes: "a" matches pattern, "1" does not
    ks_a = MagicMock()
    ks_a.characters = "a"
    ks_1 = MagicMock()
    ks_1.characters = "1"

    mock_mon = AsyncMock()
    mock_mon.async_get = AsyncMock(side_effect=[ks_a, ks_1, KeyboardInterrupt])
    mock_mon.__aenter__ = AsyncMock(return_value=mock_mon)
    mock_mon.__aexit__ = AsyncMock(return_value=False)
    mock_keystroke_monitor_cls.return_value = mock_mon

    result = runner.invoke(cli, ["monitor", "keystroke", "-p", "^[a-z]$"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Keystroke: a" in result.output
    assert "Keystroke: 1" not in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_monitor_output_with_pattern(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test monitor output with pattern filters lines."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    line0 = MagicMock()
    line0.string = "INFO: all good"
    line1 = MagicMock()
    line1.string = "ERROR: something failed"
    contents = MagicMock()
    contents.number_of_lines = 2
    contents.line = MagicMock(side_effect=lambda i: [line0, line1][i])
    mock_session.async_get_screen_contents = AsyncMock(return_value=contents)

    result = runner.invoke(cli, ["monitor", "output", "-p", "ERROR"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "ERROR: something failed" in result.output
    assert "INFO: all good" not in result.output
