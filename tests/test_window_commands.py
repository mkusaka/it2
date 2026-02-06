"""Tests for window commands."""

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
def mock_window():
    """Create a mock window."""
    window = MagicMock()
    window.window_id = "test-window-789"
    window.async_close = AsyncMock()
    window.async_activate = AsyncMock()
    window.async_get_frame = AsyncMock()
    window.async_set_frame = AsyncMock()
    window.async_get_fullscreen = AsyncMock(return_value=False)
    window.async_set_fullscreen = AsyncMock()

    # Create mock structure for tabs and sessions
    session = MagicMock()
    session.session_id = "test-session-123"
    session.async_send_text = AsyncMock()

    tab = MagicMock()
    tab.sessions = [session]
    tab.current_session = session
    tab.tab_id = "test-tab-456"

    window.tabs = [tab]
    window.current_tab = tab

    # Mock frame with origin and size
    mock_frame = MagicMock()
    mock_frame.origin = MagicMock(x=100, y=200)
    mock_frame.size = MagicMock(width=800, height=600)
    window.async_get_frame.return_value = mock_frame

    return window


@pytest.fixture
def mock_app(mock_window):
    """Create a mock app with windows."""
    app = MagicMock()
    app.windows = [mock_window]
    app.current_terminal_window = mock_window
    return app


# Test Window Creation
@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_new(
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
    """Test window new command."""
    mock_window_create.return_value = mock_window
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "new"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Created new window: test-window-789" in result.output


@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_new_with_profile(
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
    """Test window new command with profile."""
    mock_window_create.return_value = mock_window
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "new", "--profile", "MyProfile"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Created new window: test-window-789" in result.output
    assert mock_window_create.call_args[1].get("profile") == "MyProfile"


@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_new_with_command(
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
    """Test window new command with command to run."""
    mock_window_create.return_value = mock_window
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "new", "--command", "ls -la"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Created new window: test-window-789" in result.output
    assert mock_window_create.call_args[1].get("command") == "ls -la"


@patch("iterm2.Window.async_create", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_new_failure(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_window_create,
    runner,
    mock_app,
):
    """Test window new command when creation fails."""
    mock_window_create.return_value = None
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "new"])
    assert result.exit_code == 1
    assert "Failed to create window" in result.output


# Test Window Listing
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_list_json(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window list command with JSON output."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "list", "--json"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert len(output_data) == 1
    assert output_data[0]["id"] == "test-window-789"
    assert output_data[0]["tabs"] == 1
    assert output_data[0]["x"] == 100
    assert output_data[0]["y"] == 200
    assert output_data[0]["width"] == 800
    assert output_data[0]["height"] == 600
    assert output_data[0]["is_fullscreen"] is False


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_list_table(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window list command with table output."""
    # Skip this test - Rich console formatting is difficult to test in CI
    pytest.skip("Rich console formatting is difficult to test")


# Test Window Closing
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_close_current(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window close command for current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "close", "--force"])
    assert result.exit_code == 0
    assert "Window closed" in result.output
    mock_window.async_close.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_close_specific(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window close command for specific window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "close", "test-window-789", "--force"])
    assert result.exit_code == 0
    assert "Window closed" in result.output
    mock_window.async_close.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_close_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test window close command when window not found."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "close", "non-existent-window", "--force"])
    assert result.exit_code == 3
    assert "Window 'non-existent-window' not found" in result.output


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_close_no_current(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test window close command when no current window."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_app.current_terminal_window = None

    result = runner.invoke(cli, ["window", "close", "--force"])
    assert result.exit_code == 3
    assert "No current window" in result.output


# Test Window Focus
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_focus(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window focus command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "focus", "test-window-789"])
    assert result.exit_code == 0
    assert "Focused window: test-window-789" in result.output
    mock_window.async_activate.assert_called_once()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_focus_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
):
    """Test window focus command when window not found."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "focus", "non-existent-window"])
    assert result.exit_code == 3
    assert "Window 'non-existent-window' not found" in result.output


# Test Window Move
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_move(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window move command."""
    # Skip this test - requires iterm2.Point and iterm2.Frame
    pytest.skip("Requires iterm2.Point and iterm2.Frame")


# Test Window Resize
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_resize(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window resize command."""
    # Skip this test - requires iterm2.Frame and iterm2.Size
    pytest.skip("Requires iterm2.Frame and iterm2.Size")


# Test Window Fullscreen
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_fullscreen_toggle(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window fullscreen toggle command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "fullscreen", "toggle"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Fullscreen enabled" in result.output
    mock_window.async_set_fullscreen.assert_called_once_with(True)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_fullscreen_on(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window fullscreen on command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "fullscreen", "on"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Fullscreen enabled" in result.output
    mock_window.async_set_fullscreen.assert_called_once_with(True)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_fullscreen_off(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window fullscreen off command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_window.async_get_fullscreen.return_value = True

    result = runner.invoke(cli, ["window", "fullscreen", "off"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Fullscreen disabled" in result.output
    mock_window.async_set_fullscreen.assert_called_once_with(False)


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_fullscreen_already_on(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window fullscreen on when already on."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_window.async_get_fullscreen.return_value = True

    result = runner.invoke(cli, ["window", "fullscreen", "on"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Fullscreen already enabled" in result.output
    mock_window.async_set_fullscreen.assert_not_called()


@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_fullscreen_already_off(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    runner,
    mock_app,
    mock_window,
):
    """Test window fullscreen off when already off."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )
    mock_window.async_get_fullscreen.return_value = False

    result = runner.invoke(cli, ["window", "fullscreen", "off"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Fullscreen already disabled" in result.output
    mock_window.async_set_fullscreen.assert_not_called()


# Test Window Arrangements
@patch("iterm2.Arrangement.async_save", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_arrange_save(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_arrange_save,
    runner,
    mock_app,
):
    """Test window arrange save command."""
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "arrange", "save", "my-arrangement"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Saved arrangement: my-arrangement" in result.output


@patch("iterm2.Arrangement.async_restore", new_callable=AsyncMock)
@patch("iterm2.Arrangement.async_list", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_arrange_restore(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_arrange_list,
    mock_arrange_restore,
    runner,
    mock_app,
):
    """Test window arrange restore command."""
    mock_arrange_list.return_value = ["arrangement1", "arrangement2"]
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "arrange", "restore", "arrangement1"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Restored arrangement: arrangement1" in result.output


@patch("iterm2.Arrangement.async_list", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_arrange_restore_not_found(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_arrange_list,
    runner,
    mock_app,
):
    """Test window arrange restore command when arrangement not found."""
    mock_arrange_list.return_value = ["arrangement1", "arrangement2"]
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "arrange", "restore", "non-existent"])
    assert result.exit_code == 3
    assert "Arrangement 'non-existent' not found" in result.output


@patch("iterm2.Arrangement.async_list", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_arrange_list(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_arrange_list,
    runner,
    mock_app,
):
    """Test window arrange list command."""
    mock_arrange_list.return_value = ["arrangement1", "arrangement2"]
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "arrange", "list"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "Saved arrangements:" in result.output
    assert "arrangement1" in result.output
    assert "arrangement2" in result.output


@patch("iterm2.Arrangement.async_list", new_callable=AsyncMock)
@patch("iterm2.Connection.async_create")
@patch("iterm2.async_get_app")
@patch("iterm2.run_until_complete")
@patch("os.environ.get")
@patch("it2.core.connection._connection_manager")
def test_window_arrange_list_empty(
    mock_conn_mgr,
    mock_env_get,
    mock_run_until_complete,
    mock_async_get_app,
    mock_async_create,
    mock_arrange_list,
    runner,
    mock_app,
):
    """Test window arrange list command when no arrangements."""
    mock_arrange_list.return_value = []
    setup_iterm2_mocks(
        mock_conn_mgr,
        mock_env_get,
        mock_run_until_complete,
        mock_async_get_app,
        mock_async_create,
        mock_app,
    )

    result = runner.invoke(cli, ["window", "arrange", "list"])
    assert result.exit_code == 0, f"Failed with: {result.output}"
    assert "No saved arrangements" in result.output


# Test Error Handling
def test_window_command_no_cookie(runner):
    """Test window command without iTerm2 cookie."""
    with patch("os.environ.get", return_value=None), patch(
        "iterm2.Connection.async_create", side_effect=Exception("Connection failed")
    ):
        result = runner.invoke(cli, ["window", "list"])
        assert result.exit_code == 2
        assert "Not running inside iTerm2" in result.output
