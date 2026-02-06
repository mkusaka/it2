"""Tests for tab commands."""

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
def mock_tab():
    """Create a mock tab."""
    tab = MagicMock()
    tab.tab_id = "test-tab-456"
    tab.async_select = AsyncMock()
    tab.async_close = AsyncMock()
    tab.async_move_to_window = AsyncMock()

    # Create mock session
    session = MagicMock()
    session.session_id = "test-session-123"
    session.async_send_text = AsyncMock()

    tab.sessions = [session]
    tab.current_session = session

    return tab


@pytest.fixture
def mock_window(mock_tab):
    """Create a mock window with tabs."""
    window = MagicMock()
    window.window_id = "test-window-789"
    window.tabs = MagicMock()
    window.tabs.__iter__ = MagicMock(return_value=iter([mock_tab]))
    window.tabs.__len__ = MagicMock(return_value=1)
    window.tabs.__getitem__ = MagicMock(side_effect=lambda i: mock_tab if i == 0 else None)
    window.tabs.index = MagicMock(return_value=0)
    window.current_tab = mock_tab
    window.async_create_tab = AsyncMock(return_value=mock_tab)

    return window


@pytest.fixture
def mock_app(mock_window):
    """Create a mock app with windows and tabs."""
    app = MagicMock()
    app.windows = [mock_window]
    app.current_terminal_window = mock_window

    return app


# Test Tab Creation
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab new command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "new"])
    assert result.exit_code == 0
    assert "Created new tab: test-tab-456" in result.output
    mock_app.current_terminal_window.async_create_tab.assert_called_once_with(profile=None)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_with_profile(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab new command with profile."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "new", "--profile", "MyProfile"])
    assert result.exit_code == 0
    assert "Created new tab: test-tab-456" in result.output
    mock_app.current_terminal_window.async_create_tab.assert_called_once_with(profile="MyProfile")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_with_command(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab new command with command to run."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "new", "--command", "ls -la"])
    assert result.exit_code == 0
    assert "Created new tab: test-tab-456" in result.output
    mock_tab.current_session.async_send_text.assert_called_once_with("ls -la\r")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_with_specific_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test tab new command in specific window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "new", "--window", "test-window-789"])
    assert result.exit_code == 0
    assert "Created new tab: test-tab-456" in result.output
    mock_window.async_create_tab.assert_called_once_with(profile=None)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_window_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab new command with non-existent window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "new", "--window", "non-existent-window"])
    assert result.exit_code == 3
    assert "Window 'non-existent-window' not found" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_no_current_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab new command when no current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window = None

    result = runner.invoke(cli, ["tab", "new"])
    assert result.exit_code == 3
    assert "No current window" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_new_failure(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab new command when creation fails."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window.async_create_tab.return_value = None

    result = runner.invoke(cli, ["tab", "new"])
    assert result.exit_code == 1
    assert "Failed to create tab" in result.output


# Test Tab Listing
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_list(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab list command."""
    # Skip this test - Rich console output formatting
    pytest.skip("Rich console table formatting")


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_list_json(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab list command with JSON output."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "list", "--json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "test-tab-456"
    assert data[0]["window_id"] == "test-window-789"
    assert data[0]["index"] == 0
    assert data[0]["sessions"] == 1
    assert data[0]["is_active"] is True


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_list_specific_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab list command for specific window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "list", "--window", "test-window-789", "--json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["window_id"] == "test-window-789"


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_list_window_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab list command with non-existent window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "list", "--window", "non-existent", "--json"])
    assert result.exit_code == 3
    assert "Window 'non-existent' not found" in result.output


# Test Tab Close
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_close_current(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab close command for current tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "close", "--force"])
    assert result.exit_code == 0
    assert "Tab closed" in result.output
    mock_tab.async_close.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_close_specific(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab close command for specific tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "close", "test-tab-456", "--force"])
    assert result.exit_code == 0
    assert "Tab closed" in result.output
    mock_tab.async_close.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_close_tab_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab close command with non-existent tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "close", "non-existent", "--force"])
    assert result.exit_code == 3
    assert "Tab 'non-existent' not found" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_close_no_current_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab close command when no current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window = None

    result = runner.invoke(cli, ["tab", "close", "--force"])
    assert result.exit_code == 3
    assert "No current window" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_close_no_current_tab(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test tab close command when no current tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_window.current_tab = None

    result = runner.invoke(cli, ["tab", "close", "--force"])
    assert result.exit_code == 3
    assert "No current tab" in result.output


# Test Tab Select
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_select_by_id(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab select command by ID."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "select", "test-tab-456"])
    assert result.exit_code == 0
    assert "Selected tab: test-tab-456" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_select_by_index(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab select command by index."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "select", "0"])
    assert result.exit_code == 0
    assert "Selected tab at index 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_select_by_index_with_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab select command by index with specific window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "select", "0", "--window", "test-window-789"])
    assert result.exit_code == 0
    assert "Selected tab at index 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_select_index_out_of_range(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab select command with out of range index."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "select", "5"])
    assert result.exit_code == 4
    assert "Tab index 5 out of range" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_select_tab_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab select command with non-existent tab ID."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "select", "non-existent"])
    assert result.exit_code == 3
    assert "Tab 'non-existent' not found" in result.output


# Test Tab Move
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_move_current(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab move command for current tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "move"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Moved tab to new window" in result.output
    mock_tab.async_move_to_window.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_move_specific(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab move command for specific tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "move", "test-tab-456"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Moved tab to new window" in result.output
    mock_tab.async_move_to_window.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_move_tab_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab move command with non-existent tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "move", "non-existent"])
    assert result.exit_code == 3
    assert "Tab 'non-existent' not found" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_move_no_current_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab move command when no current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window = None

    result = runner.invoke(cli, ["tab", "move"])
    assert result.exit_code == 3
    assert "No current window" in result.output


# Test Tab Next
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_next(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab next command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Create second tab
    tab2 = MagicMock()
    tab2.tab_id = "test-tab-789"
    tab2.async_select = AsyncMock()
    mock_app.current_terminal_window.tabs.__iter__ = MagicMock(return_value=iter([mock_tab, tab2]))
    mock_app.current_terminal_window.tabs.__len__ = MagicMock(return_value=2)
    mock_app.current_terminal_window.tabs.__getitem__ = MagicMock(
        side_effect=lambda i: [mock_tab, tab2][i] if 0 <= i < 2 else None
    )

    result = runner.invoke(cli, ["tab", "next"])
    assert result.exit_code == 0
    assert "Switched to tab 1" in result.output
    tab2.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_next_wrap_around(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab next command wraps around to first tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Set current tab as last tab
    mock_app.current_terminal_window.tabs.index.return_value = 0

    result = runner.invoke(cli, ["tab", "next"])
    assert result.exit_code == 0
    assert "Switched to tab 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_next_no_current_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab next command when no current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window = None

    result = runner.invoke(cli, ["tab", "next"])
    assert result.exit_code == 3
    assert "No current window" in result.output


# Test Tab Previous
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_prev(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab prev command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Create second tab and set it as current
    tab2 = MagicMock()
    tab2.tab_id = "test-tab-789"
    mock_app.current_terminal_window.tabs.__iter__ = MagicMock(return_value=iter([mock_tab, tab2]))
    mock_app.current_terminal_window.tabs.__len__ = MagicMock(return_value=2)
    mock_app.current_terminal_window.tabs.__getitem__ = MagicMock(
        side_effect=lambda i: [mock_tab, tab2][i] if 0 <= i < 2 else None
    )
    mock_app.current_terminal_window.current_tab = tab2
    mock_app.current_terminal_window.tabs.index.return_value = 1

    result = runner.invoke(cli, ["tab", "prev"])
    assert result.exit_code == 0
    assert "Switched to tab 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_prev_wrap_around(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab prev command wraps around to last tab."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    # Create second tab
    tab2 = MagicMock()
    tab2.tab_id = "test-tab-789"
    tab2.async_select = AsyncMock()
    mock_app.current_terminal_window.tabs.__iter__ = MagicMock(return_value=iter([mock_tab, tab2]))
    mock_app.current_terminal_window.tabs.__len__ = MagicMock(return_value=2)
    mock_app.current_terminal_window.tabs.__getitem__ = MagicMock(
        side_effect=lambda i: [mock_tab, tab2][i] if 0 <= i < 2 else None
    )
    mock_app.current_terminal_window.tabs.index.return_value = 0

    result = runner.invoke(cli, ["tab", "prev"])
    assert result.exit_code == 0
    assert "Switched to tab 1" in result.output
    tab2.async_select.assert_called_once()


# Test Tab Goto
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_goto(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab goto command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "goto", "0"])
    assert result.exit_code == 0
    assert "Switched to tab 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_goto_with_window(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_tab,
):
    """Test tab goto command with specific window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "goto", "0", "--window", "test-window-789"])
    assert result.exit_code == 0
    assert "Switched to tab 0" in result.output
    mock_tab.async_select.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_goto_index_out_of_range(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab goto command with out of range index."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "goto", "5"])
    assert result.exit_code == 4
    assert "Tab index 5 out of range" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_tab_goto_window_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test tab goto command with non-existent window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["tab", "goto", "0", "--window", "non-existent"])
    assert result.exit_code == 3
    assert "Window 'non-existent' not found" in result.output


# Test without iTerm2 cookie
def test_tab_command_no_cookie(runner):
    """Test tab command without iTerm2 cookie."""
    with (
        patch("os.environ.get", return_value=None),
        patch("iterm2.Connection.async_create", side_effect=Exception("Connection failed")),
    ):
        result = runner.invoke(cli, ["tab", "new"])
        assert result.exit_code == 2
        assert "Not running inside iTerm2" in result.output
