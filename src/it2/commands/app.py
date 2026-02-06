"""Application-level commands for iTerm2 CLI."""

from typing import List, Optional

import click
import iterm2

from ..core.connection import run_command
from ..core.errors import handle_error

# Theme value mapping for PreferenceKey.THEME
_THEME_MAP = {
    "light": 0,
    "dark": 1,
    "light-hc": 2,
    "dark-hc": 3,
    "automatic": 4,
    "minimal": 5,
}
_THEME_NAMES = {v: k for k, v in _THEME_MAP.items()}

# Re-usable menu item identifiers
_MENU_HIDE = "Hide iTerm2"
_MENU_QUIT = "Quit iTerm2"


@click.group()
def app() -> None:
    """Control iTerm2 application."""


@app.command()
@run_command
async def activate(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Activate iTerm2 (bring to front)."""
    await app.async_activate()
    click.echo("iTerm2 activated")


@app.command()
@run_command
async def hide(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Hide iTerm2."""
    await iterm2.MainMenu.async_select_menu_item(connection, _MENU_HIDE)
    click.echo("iTerm2 hidden")


@app.command("quit")
@click.option("--force", "-f", is_flag=True, help="Force quit without confirmation")
@run_command
async def quit_app(force: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Quit iTerm2."""
    if not force:
        click.confirm("Quit iTerm2?", abort=True)

    await iterm2.MainMenu.async_select_menu_item(connection, _MENU_QUIT)
    click.echo("iTerm2 quit command sent")


@app.group()
def broadcast() -> None:
    """Input broadcasting commands."""


@broadcast.command("on")
@run_command
async def broadcast_on(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Enable input broadcasting to all sessions in current tab."""
    # Get current window
    window = app.current_terminal_window
    if not window:
        handle_error("No current window", 3)

    # Enable broadcasting for current tab
    tab = window.current_tab
    if not tab:
        handle_error("No current tab", 3)

    domain = iterm2.BroadcastDomain()
    for s in tab.sessions:
        domain.add_session(s)

    await iterm2.async_set_broadcast_domains(connection, [domain])
    click.echo("Broadcasting enabled for current tab")


@broadcast.command("off")
@run_command
async def broadcast_off(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Disable input broadcasting."""
    await iterm2.async_set_broadcast_domains(connection, [])
    click.echo("Broadcasting disabled")


@broadcast.command("add")
@click.argument("session_ids", nargs=-1, required=True)
@run_command
async def broadcast_add(
    session_ids: List[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Create broadcast group with specified sessions."""
    # Verify all sessions exist
    sessions = []
    for sid in session_ids:
        session = app.get_session_by_id(sid)
        if not session:
            handle_error(f"Session '{sid}' not found", 3)
        sessions.append(session)

    # Create a broadcast domain with the specified sessions
    domain = iterm2.BroadcastDomain()
    for session in sessions:
        domain.add_session(session)

    await iterm2.async_set_broadcast_domains(connection, [domain])
    click.echo(f"Created broadcast group with {len(sessions)} sessions")


@app.command("version")
@run_command
async def version(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Show iTerm2 version."""
    ver = await iterm2.async_get_preference(connection, iterm2.PreferenceKey.ITERM_VERSION)
    if ver:
        click.echo(f"iTerm2 version: {ver}")
    else:
        click.echo("iTerm2 version: unknown")


@app.command("theme")
@click.argument("value", required=False, type=click.Choice(list(_THEME_MAP.keys())))
@run_command
async def theme(value: Optional[str], connection: iterm2.Connection, app: iterm2.App) -> None:
    """Show or set iTerm2 theme.

    Without VALUE, shows the current theme. With VALUE, sets the theme.
    """
    if value is None:
        # Show current theme
        attributes = await app.async_get_theme()
        click.echo(f"Current theme: {', '.join(attributes)}")
    else:
        # Set theme
        theme_int = _THEME_MAP[value]
        await iterm2.async_set_preference(connection, iterm2.PreferenceKey.THEME, theme_int)
        click.echo(f"Theme set to: {value}")


@app.command("get-focus")
@run_command
async def get_focus(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Get information about the currently focused element."""
    # Get current window
    window = app.current_terminal_window
    if window:
        click.echo(f"Current window: {window.window_id}")

        # Get current tab
        tab = window.current_tab
        if tab:
            click.echo(f"Current tab: {tab.tab_id}")

            # Get current session
            session = tab.current_session
            if session:
                click.echo(f"Current session: {session.session_id}")

                # Get session info
                name = await session.async_get_variable("session.name")
                if name:
                    click.echo(f"Session name: {name}")
            else:
                click.echo("No current session")
        else:
            click.echo("No current tab")
    else:
        click.echo("No current window")
