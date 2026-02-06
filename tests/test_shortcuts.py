"""Tests for shortcut commands — verify shortcuts invoke the same logic as full commands."""

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
    return CliRunner()


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.session_id = "test-session-123"
    session.async_send_text = AsyncMock()
    session.async_split_pane = AsyncMock()
    session.grid_size = MagicMock(width=80, height=24)
    return session


@pytest.fixture
def mock_app(mock_session):
    app = MagicMock()

    tab = MagicMock()
    tab.sessions = [mock_session]
    tab.current_session = mock_session

    window = MagicMock()
    window.tabs = [tab]
    window.current_tab = tab

    app.windows = [window]
    app.current_terminal_window = window
    app.get_session_by_id = MagicMock(return_value=mock_session)

    return app


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_send_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 send' shortcut invokes session send."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["send", "Hello, World!"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("Hello, World!")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_run_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 run' shortcut invokes session run."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["run", "ls -la"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("ls -la\r")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_clear_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 clear' shortcut invokes session clear."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["clear"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("\x0c")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_split_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 split' shortcut invokes session split."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["split"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=False, profile=None)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_vsplit_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 vsplit' shortcut invokes session split --vertical."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["vsplit"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=True, profile=None)
