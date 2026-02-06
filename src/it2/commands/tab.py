"""Tab commands for iTerm2 CLI."""

import json
from typing import Optional

import click
import iterm2
from rich.console import Console
from rich.table import Table

from ..core.connection import run_command
from ..core.errors import handle_error

console = Console()


@click.group()
def tab() -> None:
    """Manage iTerm2 tabs."""


@tab.command()
@click.option("--profile", "-p", help="Profile to use for new tab")
@click.option("--window", "-w", help="Window ID to create tab in (default: current)")
@click.option("--command", "-c", help="Command to run in new tab")
@run_command
async def new(
    profile: Optional[str],
    window: Optional[str],
    command: Optional[str],
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Create new tab."""
    if window:
        # Find specific window
        target_window = None
        for w in app.windows:
            if w.window_id == window:
                target_window = w
                break

        if not target_window:
            handle_error(f"Window '{window}' not found", 3)
    else:
        # Use current window
        target_window = app.current_terminal_window
        if not target_window:
            handle_error("No current window", 3)

    tab = await target_window.async_create_tab(profile=profile)

    if tab:
        click.echo(f"Created new tab: {tab.tab_id}")

        if command:
            # Run command in the new tab's session
            session = tab.current_session
            if session:
                await session.async_send_text(command + "\r")
    else:
        handle_error("Failed to create tab")


@tab.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--window", "-w", help="Window ID to list tabs from")
@run_command
async def list_tabs(
    as_json: bool, window: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """List all tabs."""
    tabs_data = []

    if window:
        # List tabs from specific window
        target_window = None
        for w in app.windows:
            if w.window_id == window:
                target_window = w
                break

        if not target_window:
            handle_error(f"Window '{window}' not found", 3)

        windows = [target_window]
    else:
        # List all tabs from all windows
        windows = app.windows

    for win in windows:
        for idx, t in enumerate(win.tabs):
            sessions_count = len(t.sessions)
            data = {
                "id": t.tab_id,
                "window_id": win.window_id,
                "index": idx,
                "sessions": sessions_count,
                "is_active": t == win.current_tab,
            }
            tabs_data.append(data)

    if as_json:
        click.echo(json.dumps(tabs_data, indent=2))
    else:
        table = Table(title="iTerm2 Tabs")
        table.add_column("Tab ID", style="cyan")
        table.add_column("Window ID", style="green")
        table.add_column("Index", style="yellow")
        table.add_column("Sessions", style="dim")
        table.add_column("Active", style="red")

        for data in tabs_data:
            active = "✓" if data["is_active"] else ""
            table.add_row(
                str(data["id"]),
                str(data["window_id"]),
                str(data["index"]),
                str(data["sessions"]),
                active,
            )

        console.print(table)


@tab.command()
@click.argument("tab_id", required=False)
@click.option("--force", "-f", is_flag=True, help="Force close without confirmation")
@run_command
async def close(
    tab_id: Optional[str], force: bool, connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Close tab."""
    if tab_id:
        # Find specific tab
        target_tab = None
        for window in app.windows:
            for tab in window.tabs:
                if tab.tab_id == tab_id:
                    target_tab = tab
                    break
            if target_tab:
                break

        if not target_tab:
            handle_error(f"Tab '{tab_id}' not found", 3)
    else:
        # Use current tab
        current_window = app.current_terminal_window
        if not current_window:
            handle_error("No current window", 3)

        target_tab = current_window.current_tab
        if not target_tab:
            handle_error("No current tab", 3)

    if not force:
        click.confirm(f"Close tab {target_tab.tab_id}?", abort=True)

    await target_tab.async_close()
    click.echo("Tab closed")


@tab.command()
@click.argument("tab_id_or_index", required=True)
@click.option("--window", "-w", help="Window ID (for index-based selection)")
@run_command
async def select(
    tab_id_or_index: str, window: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Select tab by ID or index."""
    try:
        # Try to parse as index
        index = int(tab_id_or_index)

        # Index-based selection
        if window:
            target_window = None
            for w in app.windows:
                if w.window_id == window:
                    target_window = w
                    break

            if not target_window:
                handle_error(f"Window '{window}' not found", 3)
        else:
            target_window = app.current_terminal_window
            if not target_window:
                handle_error("No current window", 3)

        if 0 <= index < len(target_window.tabs):
            target_tab = target_window.tabs[index]
            await target_tab.async_select()
            click.echo(f"Selected tab at index {index}")
        else:
            handle_error(f"Tab index {index} out of range", 4)

    except ValueError:
        # ID-based selection
        target_tab = None
        for w in app.windows:
            for t in w.tabs:
                if t.tab_id == tab_id_or_index:
                    target_tab = t
                    break
            if target_tab:
                break

        if not target_tab:
            handle_error(f"Tab '{tab_id_or_index}' not found", 3)

        await target_tab.async_select()
        click.echo(f"Selected tab: {tab_id_or_index}")


@tab.command()
@click.argument("tab_id", required=False)
@run_command
async def move(tab_id: Optional[str], connection: iterm2.Connection, app: iterm2.App) -> None:
    """Move tab to its own new window."""
    if tab_id:
        # Find specific tab
        target_tab = None
        for window in app.windows:
            for t in window.tabs:
                if t.tab_id == tab_id:
                    target_tab = t
                    break
            if target_tab:
                break

        if not target_tab:
            handle_error(f"Tab '{tab_id}' not found", 3)
    else:
        # Use current tab
        target_window = app.current_terminal_window
        if not target_window:
            handle_error("No current window", 3)

        target_tab = target_window.current_tab
        if not target_tab:
            handle_error("No current tab", 3)

    # Move tab to its own new window
    await target_tab.async_move_to_window()
    click.echo("Moved tab to new window")


@tab.command("next")
@run_command
async def next_tab(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Switch to next tab."""
    window = app.current_terminal_window
    if not window:
        handle_error("No current window", 3)

    current_tab = window.current_tab
    if not current_tab:
        handle_error("No current tab", 3)

    # Find current tab index
    current_index = window.tabs.index(current_tab)
    next_index = (current_index + 1) % len(window.tabs)

    # Select next tab
    await window.tabs[next_index].async_select()
    click.echo(f"Switched to tab {next_index}")


@tab.command()
@run_command
async def prev(connection: iterm2.Connection, app: iterm2.App) -> None:
    """Switch to previous tab."""
    window = app.current_terminal_window
    if not window:
        handle_error("No current window", 3)

    current_tab = window.current_tab
    if not current_tab:
        handle_error("No current tab", 3)

    # Find current tab index
    current_index = window.tabs.index(current_tab)
    prev_index = (current_index - 1) % len(window.tabs)

    # Select previous tab
    await window.tabs[prev_index].async_select()
    click.echo(f"Switched to tab {prev_index}")


@tab.command()
@click.argument("index", type=int)
@click.option("--window", "-w", help="Window ID (default: current)")
@run_command
async def goto(
    index: int, window: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Go to tab by index."""
    if window:
        target_window = None
        for w in app.windows:
            if w.window_id == window:
                target_window = w
                break

        if not target_window:
            handle_error(f"Window '{window}' not found", 3)
    else:
        target_window = app.current_terminal_window
        if not target_window:
            handle_error("No current window", 3)

    if 0 <= index < len(target_window.tabs):
        await target_window.tabs[index].async_select()
        click.echo(f"Switched to tab {index}")
    else:
        handle_error(f"Tab index {index} out of range", 4)
