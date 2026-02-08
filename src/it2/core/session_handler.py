"""Session handling utilities for iTerm2 CLI."""

import re
import sys

from iterm2 import App, Session

_UUID_PATTERN = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
_ITERM_SESSION_ID_RE = re.compile(rf"^w\d+t\d+p\d+:(?P<uuid>{_UUID_PATTERN})$")
_TERMID_RE = re.compile(rf"^w\d+t\d+p\d+\.(?P<uuid>{_UUID_PATTERN})$")


def normalize_session_id(session_id: str | None) -> str | None:
    """Normalize session ID aliases to a canonical UUID when possible.

    Why this exists:
      iTerm2 APIs like ``app.get_session_by_id`` expect a bare UUID, but users
      and shell environments often provide aliases such as ``ITERM_SESSION_ID``
      (``w0t0p0:UUID``) or termid-like values (``w0t0p0.UUID``).

    When this is needed:
      Use this before any session lookup that accepts user-provided IDs
      (CLI arguments, environment-derived values, clipboard-pasted IDs).
    """
    if session_id is None:
        return None

    if session_id in {"active", "all"}:
        return session_id

    match = _ITERM_SESSION_ID_RE.match(session_id)
    if match:
        return match.group("uuid")

    match = _TERMID_RE.match(session_id)
    if match:
        return match.group("uuid")

    return session_id


def get_session_by_id(app: App, session_id: str | None) -> Session | None:
    """Get a session by ID while accepting common iTerm2 alias formats.

    This centralizes lookup behavior so command handlers do not each need to
    remember which ID shape is accepted by iTerm2's Python API.
    """
    if session_id is None:
        return None

    normalized = normalize_session_id(session_id)
    if normalized is None:
        return None

    session = app.get_session_by_id(normalized)
    if session:
        return session

    # Fallback for unexpected future formats where normalization is too strict.
    if normalized != session_id:
        return app.get_session_by_id(session_id)
    return None


async def get_target_sessions(
    app: App, session_id: str | None = None, all_sessions: bool = False
) -> list[Session]:
    """Get target sessions based on the provided criteria.

    Args:
        app: iTerm2 application instance
        session_id: Specific session ID or 'active' for current session
        all_sessions: If True, return all sessions

    Returns:
        List of target sessions
    """
    if all_sessions or session_id == "all":
        # Get all sessions
        sessions = []
        for window in app.windows:
            for tab in window.tabs:
                sessions.extend(tab.sessions)
        return sessions

    if session_id and session_id != "active":
        # Get specific session by ID
        session = get_session_by_id(app, session_id)
        if not session:
            print(f"Error: Session '{session_id}' not found", file=sys.stderr)
            sys.exit(3)
        return [session]

    # Get active session (default)
    current_window = app.current_terminal_window
    if not current_window:
        print("Error: No active window found", file=sys.stderr)
        sys.exit(3)
    current_tab = current_window.current_tab
    if not current_tab:
        print("Error: No active tab found", file=sys.stderr)
        sys.exit(3)
    current_session = current_tab.current_session
    if not current_session:
        print("Error: No active session found", file=sys.stderr)
        sys.exit(3)
    return [current_session]


async def get_session_info(session: Session) -> dict:
    """Get information about a session.

    Args:
        session: Session instance

    Returns:
        Dictionary with session information
    """
    return {
        "id": session.session_id,
        "name": await session.async_get_variable("session.name") or "",
        "title": await session.async_get_variable("session.title") or "",
        "tty": await session.async_get_variable("session.tty") or "",
        "rows": session.grid_size.height,
        "cols": session.grid_size.width,
        "is_tmux": await session.async_get_variable("session.tmux") == "yes",
    }


async def find_session_by_name(app: App, name: str) -> Session | None:
    """Find a session by its name.

    Args:
        app: iTerm2 application instance
        name: Session name to search for

    Returns:
        Session if found, None otherwise
    """
    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                session_name = await session.async_get_variable("session.name")
                if session_name == name:
                    return session
    return None
