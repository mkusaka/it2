"""Monitoring commands for iTerm2 CLI."""

import asyncio
import re
from re import Pattern

import click
import iterm2

from ..core.connection import run_command
from ..core.errors import handle_error
from ..core.session_handler import get_target_sessions


@click.group()
def monitor() -> None:
    """Monitor iTerm2 events."""


@monitor.command()
@click.option("--follow", "-f", is_flag=True, help="Follow output continuously")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--pattern", "-p", help="Filter output by regex pattern")
@run_command
async def output(
    follow: bool,
    session: str | None,
    pattern: str | None,
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Monitor session output."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    # Compile pattern if provided
    regex: Pattern | None = None
    if pattern:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            handle_error(f"Invalid regex pattern: {e}", 4)

    if follow:
        click.echo(f"Monitoring output from session {target_session.session_id}...")
        click.echo("Press Ctrl+C to stop")

        try:
            async with target_session.get_screen_streamer() as streamer:
                while True:
                    contents = await streamer.async_get()
                    if contents is None:
                        continue
                    text_lines = [contents.line(i).string for i in range(contents.number_of_lines)]
                    text = "\n".join(text_lines)

                    if regex:
                        matching_lines = [ln for ln in text_lines if regex.search(ln)]
                        if matching_lines:
                            for ln in matching_lines:
                                click.echo(ln)
                    else:
                        if text.strip():
                            click.echo(text)
        except KeyboardInterrupt:
            click.echo("\nMonitoring stopped")
    else:
        # Just get current screen contents
        contents = await target_session.async_get_screen_contents()
        text_lines = [contents.line(i).string for i in range(contents.number_of_lines)]
        text = "\n".join(text_lines)

        if regex:
            matching_lines = [ln for ln in text_lines if regex.search(ln)]
            for ln in matching_lines:
                click.echo(ln)
        else:
            click.echo(text)


@monitor.command()
@click.option("--pattern", "-p", help="Filter keystrokes by regex pattern")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
async def keystroke(
    pattern: str | None, session: str | None, connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Monitor keystrokes."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    # Compile pattern if provided
    regex: Pattern | None = None
    if pattern:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            handle_error(f"Invalid regex pattern: {e}", 4)

    click.echo(f"Monitoring keystrokes in session {target_session.session_id}...")
    click.echo("Press Ctrl+C to stop")

    try:
        async with iterm2.KeystrokeMonitor(connection, session=target_session.session_id) as mon:
            while True:
                keystroke = await mon.async_get()
                key_str = keystroke.characters

                if regex:
                    if regex.search(key_str):
                        click.echo(f"Keystroke: {key_str}")
                else:
                    click.echo(f"Keystroke: {key_str}")
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")


@monitor.command()
@click.argument("variable_name")
@click.option("--session", "-s", help="Target session ID (default: active)")
@click.option("--app-level", is_flag=True, help="Monitor app-level variable")
@run_command
async def variable(
    variable_name: str,
    session: str | None,
    app_level: bool,
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Monitor variable changes."""
    if app_level:
        # Monitor app-level variable
        click.echo(f"Monitoring app variable '{variable_name}'...")
        scope = iterm2.VariableScopes.APP
        identifier = None

        # Get initial value
        initial_value = await app.async_get_variable(variable_name)
        click.echo(f"Current value: {initial_value}")
    else:
        # Monitor session variable
        sessions = await get_target_sessions(app, session)
        target_session = sessions[0]

        click.echo(f"Monitoring session variable '{variable_name}'...")
        scope = iterm2.VariableScopes.SESSION
        identifier = target_session.session_id

        # Get initial value
        initial_value = await target_session.async_get_variable(variable_name)
        click.echo(f"Current value: {initial_value}")

    click.echo("Press Ctrl+C to stop")

    try:
        async with iterm2.VariableMonitor(connection, scope, variable_name, identifier) as mon:
            while True:
                new_value = await mon.async_get()
                click.echo(f"Changed to: {new_value}")
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")


@monitor.command()
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
async def prompt(session: str | None, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Monitor shell prompts (requires shell integration)."""
    sessions = await get_target_sessions(app, session)
    target_session = sessions[0]

    # Check if shell integration is available
    shell_integration = await target_session.async_get_variable("user.shell_integration_installed")
    if not shell_integration:
        click.echo("Warning: Shell integration may not be installed.")
        click.echo("Install it from: iTerm2 > Install Shell Integration")

    click.echo(f"Monitoring prompts in session {target_session.session_id}...")
    click.echo("Press Ctrl+C to stop")

    try:
        async with iterm2.PromptMonitor(connection, target_session.session_id) as mon:
            while True:
                mode, value = await mon.async_get()

                if mode == iterm2.PromptMonitor.Mode.PROMPT:
                    click.echo("New prompt detected")
                elif mode == iterm2.PromptMonitor.Mode.COMMAND_START:
                    click.echo(f"Command started: {value}")
                elif mode == iterm2.PromptMonitor.Mode.COMMAND_END:
                    click.echo(f"Command finished (exit status: {value})")
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")


@monitor.command("activity")
@click.option("--all", "-a", "all_sessions", is_flag=True, help="Monitor all sessions")
@run_command
async def activity(all_sessions: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Monitor session activity."""
    if all_sessions:
        click.echo("Monitoring activity in all sessions...")
    else:
        click.echo("Monitoring activity in current session...")

    click.echo("Press Ctrl+C to stop")

    # Track session activity
    session_activity = {}

    try:
        # Monitor all sessions for activity
        while True:
            for window in app.windows:
                for tab in window.tabs:
                    for session in tab.sessions:
                        current_window = app.current_terminal_window
                        current_session = None
                        if current_window:
                            current_tab = current_window.current_tab
                            if current_tab:
                                current_session = current_tab.current_session
                        if not all_sessions and session != current_session:
                            continue

                        # Get session activity indicator
                        session_id = session.session_id
                        is_active = await session.async_get_variable("session.isActive")

                        # Check if activity changed
                        if session_id not in session_activity:
                            session_activity[session_id] = is_active
                        elif session_activity[session_id] != is_active:
                            session_activity[session_id] = is_active

                            # Get session name for display
                            name = await session.async_get_variable("session.name") or session_id

                            if is_active:
                                click.echo(f"Session active: {name}")
                            else:
                                click.echo(f"Session idle: {name}")

            # Small delay to prevent excessive CPU usage
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")
