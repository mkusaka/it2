"""Tests for session handler module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from it2.core.session_handler import (
    find_session_by_name,
    get_session_info,
    get_target_sessions,
    normalize_session_id,
)


@pytest.mark.asyncio
async def test_get_target_sessions_all():
    """Test getting all sessions."""
    # Mock app with windows, tabs, and sessions
    mock_app = MagicMock()

    # Create mock sessions
    session1 = MagicMock(session_id="session1")
    session2 = MagicMock(session_id="session2")
    session3 = MagicMock(session_id="session3")

    # Create mock structure
    tab1 = MagicMock(sessions=[session1, session2])
    tab2 = MagicMock(sessions=[session3])
    window1 = MagicMock(tabs=[tab1])
    window2 = MagicMock(tabs=[tab2])

    mock_app.windows = [window1, window2]

    # Test getting all sessions
    sessions = await get_target_sessions(mock_app, all_sessions=True)
    assert len(sessions) == 3
    assert session1 in sessions
    assert session2 in sessions
    assert session3 in sessions


@pytest.mark.asyncio
async def test_get_target_sessions_specific():
    """Test getting specific session by ID."""
    mock_app = MagicMock()

    # Create mock session
    target_session = MagicMock(session_id="target-session")
    mock_app.get_session_by_id.return_value = target_session

    # Test getting specific session
    sessions = await get_target_sessions(mock_app, session_id="target-session")
    assert len(sessions) == 1
    assert sessions[0] == target_session
    mock_app.get_session_by_id.assert_called_once_with("target-session")


@pytest.mark.asyncio
async def test_get_target_sessions_specific_iterm_session_id():
    """Test getting specific session by ITERM_SESSION_ID format."""
    mock_app = MagicMock()
    uuid = "93DC1CBF-8BA1-48B2-9C6A-834D3AECF340"
    iterm_session_id = f"w0t1p2:{uuid}"
    target_session = MagicMock(session_id=uuid)

    def lookup(session_id):
        if session_id == uuid:
            return target_session
        return None

    mock_app.get_session_by_id = MagicMock(side_effect=lookup)

    sessions = await get_target_sessions(mock_app, session_id=iterm_session_id)
    assert len(sessions) == 1
    assert sessions[0] == target_session
    mock_app.get_session_by_id.assert_called_once_with(uuid)


@pytest.mark.asyncio
async def test_get_target_sessions_specific_termid():
    """Test getting specific session by termid format."""
    mock_app = MagicMock()
    uuid = "93DC1CBF-8BA1-48B2-9C6A-834D3AECF340"
    termid = f"w0t1p2.{uuid}"
    target_session = MagicMock(session_id=uuid)

    def lookup(session_id):
        if session_id == uuid:
            return target_session
        return None

    mock_app.get_session_by_id = MagicMock(side_effect=lookup)

    sessions = await get_target_sessions(mock_app, session_id=termid)
    assert len(sessions) == 1
    assert sessions[0] == target_session
    mock_app.get_session_by_id.assert_called_once_with(uuid)


@pytest.mark.asyncio
async def test_get_target_sessions_active():
    """Test getting active session."""
    mock_app = MagicMock()

    # Create mock active session
    active_session = MagicMock(session_id="active-session")
    mock_app.current_terminal_window.current_tab.current_session = active_session

    # Test getting active session (default)
    sessions = await get_target_sessions(mock_app)
    assert len(sessions) == 1
    assert sessions[0] == active_session


@pytest.mark.asyncio
async def test_get_session_info():
    """Test getting session information."""
    # Create mock session
    mock_session = MagicMock()
    mock_session.session_id = "test-session"
    mock_session.grid_size.height = 24
    mock_session.grid_size.width = 80

    # Mock async methods
    async def mock_get_variable(name):
        variables = {
            "session.name": "Test Session",
            "session.title": "Test Title",
            "session.tty": "/dev/ttys001",
            "session.tmux": "no",
        }
        return variables.get(name)

    mock_session.async_get_variable = AsyncMock(side_effect=mock_get_variable)

    # Get session info
    info = await get_session_info(mock_session)

    assert info["id"] == "test-session"
    assert info["name"] == "Test Session"
    assert info["title"] == "Test Title"
    assert info["tty"] == "/dev/ttys001"
    assert info["rows"] == 24
    assert info["cols"] == 80
    assert info["is_tmux"] is False


@pytest.mark.asyncio
async def test_find_session_by_name():
    """Test finding session by name."""
    mock_app = MagicMock()

    # Create mock sessions with names
    session1 = MagicMock()
    session1.async_get_variable = AsyncMock(return_value="Session One")

    session2 = MagicMock()
    session2.async_get_variable = AsyncMock(return_value="Target Session")

    session3 = MagicMock()
    session3.async_get_variable = AsyncMock(return_value="Session Three")

    # Create mock structure
    tab = MagicMock(sessions=[session1, session2, session3])
    window = MagicMock(tabs=[tab])
    mock_app.windows = [window]

    # Find session by name
    found = await find_session_by_name(mock_app, "Target Session")
    assert found == session2

    # Test not found
    not_found = await find_session_by_name(mock_app, "Non-existent")
    assert not_found is None


def test_normalize_session_id():
    """Test session ID normalization helper."""
    uuid = "93DC1CBF-8BA1-48B2-9C6A-834D3AECF340"
    assert normalize_session_id(uuid) == uuid
    assert normalize_session_id(f"w0t1p2:{uuid}") == uuid
    assert normalize_session_id(f"w0t1p2.{uuid}") == uuid
    assert normalize_session_id("active") == "active"
    assert normalize_session_id("all") == "all"
    assert normalize_session_id(None) is None
