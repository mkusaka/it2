"""Tests for shortcut commands — verify shortcuts invoke the same logic as full commands."""

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
def mock_window(mock_session):
    tab = MagicMock()
    tab.tab_id = "test-tab-456"
    tab.sessions = [mock_session]
    tab.current_session = mock_session

    window = MagicMock()
    window.window_id = "test-window-789"
    window.tabs = [tab]
    window.current_tab = tab
    window.async_create_tab = AsyncMock(return_value=tab)
    return window


@pytest.fixture
def mock_app(mock_session, mock_window):
    app = MagicMock()

    app.windows = [mock_window]
    app.current_terminal_window = mock_window
    app.get_session_by_id = MagicMock(return_value=mock_session)

    return app


# ---------------------------------------------------------------------------
# send shortcut
# ---------------------------------------------------------------------------


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
def test_send_shortcut_with_all(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test 'it2 send --all' sends to all sessions."""
    session1 = MagicMock()
    session1.async_send_text = AsyncMock()
    session2 = MagicMock()
    session2.async_send_text = AsyncMock()

    tab1 = MagicMock(sessions=[session1])
    tab2 = MagicMock(sessions=[session2])
    window = MagicMock(tabs=[tab1, tab2])
    mock_app.windows = [window]

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["send", "Hello!", "--all"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Sent text to 2 sessions" in result.output
    session1.async_send_text.assert_called_once_with("Hello!")
    session2.async_send_text.assert_called_once_with("Hello!")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_send_shortcut_with_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 send --session <id>' targets a specific session."""
    mock_app.get_session_by_id = MagicMock(return_value=mock_session)

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["send", "Hello!", "--session", "test-session-123"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("Hello!")


# ---------------------------------------------------------------------------
# run shortcut
# ---------------------------------------------------------------------------


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
def test_run_shortcut_with_all(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test 'it2 run --all' runs in all sessions."""
    session1 = MagicMock()
    session1.async_send_text = AsyncMock()
    session2 = MagicMock()
    session2.async_send_text = AsyncMock()

    tab1 = MagicMock(sessions=[session1])
    tab2 = MagicMock(sessions=[session2])
    window = MagicMock(tabs=[tab1, tab2])
    mock_app.windows = [window]

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["run", "echo hi", "--all"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Executed command in 2 sessions" in result.output
    session1.async_send_text.assert_called_once_with("echo hi\r")
    session2.async_send_text.assert_called_once_with("echo hi\r")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_run_shortcut_with_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 run --session <id>' targets a specific session."""
    mock_app.get_session_by_id = MagicMock(return_value=mock_session)

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["run", "ls", "--session", "test-session-123"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("ls\r")


# ---------------------------------------------------------------------------
# clear shortcut
# ---------------------------------------------------------------------------


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
def test_clear_shortcut_with_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 clear --session <id>' targets a specific session."""
    mock_app.get_session_by_id = MagicMock(return_value=mock_session)

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["clear", "--session", "test-session-123"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_send_text.assert_called_once_with("\x0c")


# ---------------------------------------------------------------------------
# split shortcut
# ---------------------------------------------------------------------------


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
def test_split_shortcut_vertical(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 split --vertical' splits vertically."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["split", "--vertical"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=True, profile=None)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_split_shortcut_with_profile(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 split --profile <name>' uses specified profile."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["split", "--profile", "Development"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=False, profile="Development")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_split_shortcut_with_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 split --session <id>' targets a specific session."""
    mock_app.get_session_by_id = MagicMock(return_value=mock_session)

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["split", "--session", "test-session-123"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=False, profile=None)


# ---------------------------------------------------------------------------
# vsplit shortcut
# ---------------------------------------------------------------------------


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


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_vsplit_shortcut_with_profile(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 vsplit --profile <name>' uses specified profile."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["vsplit", "--profile", "Development"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=True, profile="Development")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_vsplit_shortcut_with_session(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 vsplit --session <id>' targets a specific session."""
    mock_app.get_session_by_id = MagicMock(return_value=mock_session)

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    mock_session.async_split_pane.return_value = MagicMock(session_id="new-session-456")

    result = runner.invoke(cli, ["vsplit", "--session", "test-session-123"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    mock_session.async_split_pane.assert_called_once_with(vertical=True, profile=None)


# ---------------------------------------------------------------------------
# ls shortcut
# ---------------------------------------------------------------------------


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_ls_shortcut_json(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 ls --json' lists sessions as JSON."""
    mock_session.async_get_variable = AsyncMock(
        side_effect=lambda var: {
            "session.name": "Test Session",
            "session.title": "Test Title",
            "session.tty": "/dev/ttys001",
            "session.tmux": "no",
        }.get(var)
    )

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["ls", "--json"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "test-session-123"


# ---------------------------------------------------------------------------
# new shortcut (window)
# ---------------------------------------------------------------------------


@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_new_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_window_create,
    runner,
    mock_app,
    mock_window,
):
    """Test 'it2 new' shortcut creates a new window."""
    mock_window_create.return_value = mock_window
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["new"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Created new window" in result.output


@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_new_shortcut_with_profile_and_command(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_window_create,
    runner,
    mock_app,
    mock_window,
):
    """Test 'it2 new --profile <name> --command <cmd>' passes options through."""
    mock_window_create.return_value = mock_window
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["new", "--profile", "Development", "--command", "htop"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert mock_window_create.call_args[1].get("profile") == "Development"
    assert mock_window_create.call_args[1].get("command") == "htop"


# ---------------------------------------------------------------------------
# newtab shortcut
# ---------------------------------------------------------------------------


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_newtab_shortcut(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test 'it2 newtab' shortcut creates a new tab."""
    window = mock_app.current_terminal_window

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["newtab"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    window.async_create_tab.assert_called_once_with(profile=None)
    assert "Created new tab" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_newtab_shortcut_with_profile_and_command(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_session,
):
    """Test 'it2 newtab --profile <name> --command <cmd>' passes options through."""
    window = mock_app.current_terminal_window

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["newtab", "--profile", "Development", "--command", "htop"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    window.async_create_tab.assert_called_once_with(profile="Development")
    mock_session.async_send_text.assert_called_once_with("htop\r")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_newtab_shortcut_with_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test 'it2 newtab --window <id>' creates tab in specific window."""
    window = mock_app.current_terminal_window

    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["newtab", "--window", "test-window-789"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    window.async_create_tab.assert_called_once_with(profile=None)
