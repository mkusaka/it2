"""Session commands for iTerm2 CLI."""

import json
from typing import Optional

import click
import iterm2
from rich.console import Console
from rich.table import Table

from ..core.connection import run_command, with_connection
from ..core.errors import handle_error
from ..core.session_handler import get_session_info, get_target_sessions

console = Console()


@click.group()
def session() -> None:
    """Manage iTerm2 sessions."""


@session.command("send")
@click.argument("text")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--all", "-a", "all_sessions", is_flag=True, help="Send to all sessions")
@run_command
@with_connection
async def send(
    text: str,
    session: Optional[str],
    all_sessions: bool,
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Send text to session(s) without newline."""
    sessions = await get_target_sessions(app, session, all_sessions)

    for s in sessions:
        await s.async_send_text(text)

    if len(sessions) > 1:
        click.echo(f"Sent text to {len(sessions)} sessions")


@session.command("run")
@click.argument("command")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--all", "-a", "all_sessions", is_flag=True, help="Run in all sessions")
@run_command
@with_connection
async def run(
    command: str,
    session: Optional[str],
    all_sessions: bool,
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Execute command in session(s) with newline."""
    sessions = await get_target_sessions(app, session, all_sessions)

    for s in sessions:
        await s.async_send_text(command + "\r")

    if len(sessions) > 1:
        click.echo(f"Executed command in {len(sessions)} sessions")


@session.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@run_command
@with_connection
async def list_sessions(as_json: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """List all sessions."""
    sessions_data = []

    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                info = await get_session_info(session)
                info["window_id"] = window.window_id
                info["tab_id"] = tab.tab_id
                sessions_data.append(info)

    if as_json:
        click.echo(json.dumps(sessions_data, indent=2))
    else:
        table = Table(title="iTerm2 Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Title")
        table.add_column("Size", style="dim")
        table.add_column("TTY", style="dim")

        for data in sessions_data:
            size = f"{data['cols']}x{data['rows']}"
            table.add_row(data["id"], data["name"], data["title"], size, data["tty"])

        console.print(table)


@session.command("split")
@click.option("--vertical", "-v", is_flag=True, help="Split vertically")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--profile", "-p", help="Profile to use for new pane")
@run_command
@with_connection
async def split(
    vertical: bool,
    session: Optional[str],
    profile: Optional[str],
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Split current session."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    if vertical:
        new_session = await target_session.async_split_pane(vertical=True, profile=profile)
    else:
        new_session = await target_session.async_split_pane(vertical=False, profile=profile)

    if new_session:
        click.echo(f"Created new pane: {new_session.session_id}")
    else:
        handle_error("Failed to split pane")


@session.command("close")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--force", "-f", is_flag=True, help="Force close without confirmation")
@run_command
@with_connection
async def close(
    session: Optional[str], force: bool, connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Close session."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    if not force:
        click.confirm(f"Close session {target_session.session_id}?", abort=True)

    await target_session.async_close()
    click.echo("Session closed")


@session.command("restart")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def restart(session: Optional[str], connection: iterm2.Connection, app: iterm2.App) -> None:
    """Restart session."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    await target_session.async_restart()
    click.echo("Session restarted")


@session.command("focus")
@click.argument("session_id")
@run_command
@with_connection
async def focus(session_id: str, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Focus a specific session."""
    target_session = app.get_session_by_id(session_id)
    if not target_session:
        handle_error(f"Session '{session_id}' not found", 3)

    await target_session.async_activate()
    click.echo(f"Focused session: {session_id}")


@session.command("read")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--lines", "-n", type=int, help="Number of lines to read")
@run_command
@with_connection
async def read(
    session: Optional[str], lines: Optional[int], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Display screen contents."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    # Get screen contents
    contents = await target_session.async_get_screen_contents()

    if lines is not None:
        # Get last N lines
        text_lines = contents.string_lines_ignoring_hard_newlines()
        output_lines = text_lines[-lines:] if lines < len(text_lines) else text_lines
        for line in output_lines:
            click.echo(line)
    else:
        # Output all content
        click.echo(contents.string_ignoring_hard_newlines())


@session.command("copy")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def copy(session: Optional[str], connection: iterm2.Connection, app: iterm2.App) -> None:
    """Copy selection to clipboard."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    selection = await target_session.async_get_selection()
    if selection:
        text = await target_session.async_get_selection_text(selection)
        if text:
            # Use pbcopy on macOS
            import subprocess

            subprocess.run(["/usr/bin/pbcopy"], input=text.encode(), check=True)
            click.echo("Selection copied to clipboard")
        else:
            click.echo("No text selected")
    else:
        click.echo("No selection")


@session.command("clear")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def clear(session: Optional[str], connection: iterm2.Connection, app: iterm2.App) -> None:
    """Clear screen."""
    sessions = await get_target_sessions(app, session)

    for s in sessions:
        await s.async_send_text("\x0c")  # Send Ctrl+L

    if len(sessions) > 1:
        click.echo(f"Cleared {len(sessions)} sessions")


@session.command("capture")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--history", is_flag=True, help="Include scrollback history")
@run_command
@with_connection
async def capture(
    session: Optional[str],
    output: str,
    history: bool,
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Capture screen to file."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    if history:
        # Get contents including history
        contents = await target_session.async_get_contents()
    else:
        # Get only visible contents
        contents = await target_session.async_get_screen_contents()

    # Write to file
    with open(output, "w") as f:
        f.write(contents.string_ignoring_hard_newlines())

    click.echo(f"Screen captured to: {output}")


@session.command("set-name")
@click.argument("name")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def set_name(
    name: str, session: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Set session name."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    await target_session.async_set_name(name)
    click.echo(f"Session name set to: {name}")


@session.command("get-var")
@click.argument("variable")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def get_var(
    variable: str, session: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Get session variable value."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    value = await target_session.async_get_variable(variable)
    if value is not None:
        click.echo(value)
    else:
        click.echo(f"Variable '{variable}' not set")


@session.command("set-var")
@click.argument("variable")
@click.argument("value")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
@with_connection
async def set_var(
    variable: str,
    value: str,
    session: Optional[str],
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Set session variable value."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    await target_session.async_set_variable(variable, value)
    click.echo(f"Set {variable} = {value}")
