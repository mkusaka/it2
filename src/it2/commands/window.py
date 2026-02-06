"""Window commands for iTerm2 CLI."""

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
def window() -> None:
    """Manage iTerm2 windows."""


@window.command()
@click.option("--profile", "-p", help="Profile to use for new window")
@click.option("--command", "-c", help="Command to run in new window")
@run_command
async def new(
    profile: Optional[str], command: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Create new window."""
    # iterm2 stubs type profile/command as str, but the implementation accepts None.
    # See iterm2/window.py async_create(): both default to None and are forwarded
    # to CreateTabRequest which handles None correctly.
    window = await iterm2.Window.async_create(
        connection, profile=profile, command=command  # type: ignore[arg-type]
    )

    if window:
        click.echo(f"Created new window: {window.window_id}")
    else:
        handle_error("Failed to create window")


@window.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@run_command
async def list_windows(as_json: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """List all windows."""
    windows_data = []

    for window in app.windows:
        frame = await window.async_get_frame()
        data = {
            "id": window.window_id,
            "tabs": len(window.tabs),
            "x": frame.origin.x,
            "y": frame.origin.y,
            "width": frame.size.width,
            "height": frame.size.height,
            "is_fullscreen": await window.async_get_fullscreen(),
        }
        windows_data.append(data)

    if as_json:
        click.echo(json.dumps(windows_data, indent=2))
    else:
        table = Table(title="iTerm2 Windows")
        table.add_column("Window ID", style="cyan")
        table.add_column("Tabs", style="green")
        table.add_column("Position", style="dim")
        table.add_column("Size", style="dim")
        table.add_column("Fullscreen", style="yellow")

        for data in windows_data:
            position = f"({data['x']}, {data['y']})"
            size = f"{data['width']}x{data['height']}"
            fullscreen = "Yes" if data["is_fullscreen"] else "No"

            table.add_row(str(data["id"]), str(data["tabs"]), position, size, fullscreen)

        console.print(table)


@window.command()
@click.argument("window_id", required=False)
@click.option("--force", "-f", is_flag=True, help="Force close without confirmation")
@run_command
async def close(
    window_id: Optional[str], force: bool, connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Close window."""
    if window_id:
        # Find specific window
        window = None
        for w in app.windows:
            if w.window_id == window_id:
                window = w
                break

        if not window:
            handle_error(f"Window '{window_id}' not found", 3)
    else:
        # Use current window
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

    if not force:
        click.confirm(f"Close window {window.window_id}?", abort=True)

    await window.async_close()
    click.echo("Window closed")


@window.command()
@click.argument("window_id")
@run_command
async def focus(window_id: str, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Focus a specific window."""
    window = None
    for w in app.windows:
        if w.window_id == window_id:
            window = w
            break

    if not window:
        handle_error(f"Window '{window_id}' not found", 3)

    await window.async_activate()
    click.echo(f"Focused window: {window_id}")


@window.command()
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.argument("window_id", required=False)
@run_command
async def move(
    x: int, y: int, window_id: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Move window to position."""
    if window_id:
        window = None
        for w in app.windows:
            if w.window_id == window_id:
                window = w
                break

        if not window:
            handle_error(f"Window '{window_id}' not found", 3)
    else:
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

    point = iterm2.Point(x, y)
    await window.async_set_frame(iterm2.Frame(origin=point))
    click.echo(f"Moved window to ({x}, {y})")


@window.command()
@click.argument("width", type=int)
@click.argument("height", type=int)
@click.argument("window_id", required=False)
@run_command
async def resize(
    width: int,
    height: int,
    window_id: Optional[str],
    connection: iterm2.Connection,
    app: iterm2.App,
) -> None:
    """Resize window."""
    if window_id:
        window = None
        for w in app.windows:
            if w.window_id == window_id:
                window = w
                break

        if not window:
            handle_error(f"Window '{window_id}' not found", 3)
    else:
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

    current_frame = await window.async_get_frame()
    new_frame = iterm2.Frame(origin=current_frame.origin, size=iterm2.Size(width, height))
    await window.async_set_frame(new_frame)
    click.echo(f"Resized window to {width}x{height}")


@window.command()
@click.argument("state", type=click.Choice(["on", "off", "toggle"]))
@click.argument("window_id", required=False)
@run_command
async def fullscreen(
    state: str, window_id: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Toggle fullscreen mode."""
    if window_id:
        window = None
        for w in app.windows:
            if w.window_id == window_id:
                window = w
                break

        if not window:
            handle_error(f"Window '{window_id}' not found", 3)
    else:
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

    is_fullscreen = await window.async_get_fullscreen()

    if state == "toggle":
        new_state = not is_fullscreen
    elif state == "on":
        new_state = True
    else:  # off
        new_state = False

    if new_state != is_fullscreen:
        await window.async_set_fullscreen(new_state)
        click.echo(f"Fullscreen {'enabled' if new_state else 'disabled'}")
    else:
        click.echo(f"Fullscreen already {'enabled' if is_fullscreen else 'disabled'}")


@window.group()
def arrange() -> None:
    """Window arrangement commands."""


@arrange.command("save")
@click.argument("name")
@run_command
async def arrange_save(name: str, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Save current window arrangement."""
    await iterm2.Arrangement.async_save(connection, name)
    click.echo(f"Saved arrangement: {name}")


@arrange.command("restore")
@click.argument("name")
@run_command
async def arrange_restore(name: str, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Restore window arrangement."""
    # List saved arrangements
    arrangements = await iterm2.Arrangement.async_list(connection)

    if name not in arrangements:
        handle_error(f"Arrangement '{name}' not found", 3)

    await iterm2.Arrangement.async_restore(connection, name)
    click.echo(f"Restored arrangement: {name}")


@arrange.command("list")
@run_command
async def arrange_list(connection: iterm2.Connection, app: iterm2.App) -> None:
    """List saved window arrangements."""
    arrangements = await iterm2.Arrangement.async_list(connection)

    if arrangements:
        click.echo("Saved arrangements:")
        for name in arrangements:
            click.echo(f"  - {name}")
    else:
        click.echo("No saved arrangements")
