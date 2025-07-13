"""Application-level commands for iTerm2 CLI."""

from typing import List, Optional

import click
import iterm2

from ..core.connection import run_command, with_connection
from ..core.errors import handle_error


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
    await app.async_hide()
    click.echo("iTerm2 hidden")


@app.command("quit")
@click.option("--force", "-f", is_flag=True, help="Force quit without confirmation")
@run_command
async def quit_app(force: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Quit iTerm2."""
    if not force:
        click.confirm("Quit iTerm2?", abort=True)

    # Note: This will close the connection and exit the script
    await connection.async_send_notification(
        iterm2.api_pb2.ClientOriginatedMessage.Notification(
            terminate_app_request=iterm2.api_pb2.TerminateAppRequest()
        )
    )
    click.echo("iTerm2 quit command sent")


@app.group()
def broadcast() -> None:
    """Input broadcasting commands."""


@broadcast.command("on")
@run_command
async def broadcast_on(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Enable input broadcasting to all sessions."""
    # Get current window
    window = app.current_terminal_window
    if not window:
        handle_error("No current window", 3)

    # Enable broadcasting for current tab
    tab = window.current_tab
    if not tab:
        handle_error("No current tab", 3)

    await tab.async_set_broadcast_domains(["all"])
    click.echo("Broadcasting enabled for current tab")


@broadcast.command("off")
@run_command
async def broadcast_off(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Disable input broadcasting."""
    # Get current window
    window = app.current_terminal_window
    if not window:
        handle_error("No current window", 3)

    # Disable broadcasting for current tab
    tab = window.current_tab
    if not tab:
        handle_error("No current tab", 3)

    await tab.async_set_broadcast_domains([])
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

    # Create a unique broadcast domain
    domain = f"custom_{'-'.join(session_ids[:3])}"

    # Set broadcast domain for all specified sessions
    for session in sessions:
        await session.async_set_broadcast_domains([domain])

    click.echo(f"Created broadcast group with {len(sessions)} sessions")


@app.command("version")
@run_command
async def version(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Show iTerm2 version information."""
    # Get version info
    build_number = await app.async_get_variable("buildNumber")
    version_number = await app.async_get_variable("version")

    click.echo(f"iTerm2 version: {version_number}")
    click.echo(f"Build: {build_number}")


@app.command("theme")
@click.argument("theme", type=click.Choice(["light", "dark", "auto"]))
@run_command
async def theme(theme: str, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Set iTerm2 theme."""
    theme_map = {
        "light": iterm2.Theme.LIGHT,
        "dark": iterm2.Theme.DARK,
        "auto": iterm2.Theme.AUTO,
    }

    await app.async_set_theme(theme_map[theme])
    click.echo(f"Theme set to: {theme}")


@app.command("create-hotkey-window")
@click.option("--profile", "-p", help="Profile to use")
@run_command
async def create_hotkey_window(
    profile: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Create a hotkey window."""
    window = await iterm2.HotkeyWindow.async_create(connection, profile=profile)

    if window:
        click.echo("Created hotkey window")
        click.echo("Configure hotkey in: Preferences > Keys > Hotkey Window")
    else:
        handle_error("Failed to create hotkey window")


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
