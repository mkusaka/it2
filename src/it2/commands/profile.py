"""Profile commands for iTerm2 CLI."""

import json
from typing import Optional

import click
import iterm2
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..core.connection import run_command
from ..core.errors import handle_error

console = Console()


@click.group()
def profile() -> None:
    """Manage iTerm2 profiles."""


@profile.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@run_command
async def list_profiles(as_json: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """List all profiles."""
    profiles = await iterm2.PartialProfile.async_query(connection)

    profiles_data = []
    for p in profiles:
        data = {
            "guid": p.guid,
            "name": p.name,
        }
        profiles_data.append(data)

    if as_json:
        click.echo(json.dumps(profiles_data, indent=2))
    else:
        table = Table(title="iTerm2 Profiles")
        table.add_column("GUID", style="cyan")
        table.add_column("Name", style="green")

        for data in profiles_data:
            table.add_row(data["guid"], data["name"])

        console.print(table)


@profile.command()
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@run_command
async def show(name: str, as_json: bool, connection: iterm2.Connection, app: iterm2.App) -> None:
    """Show profile details."""
    # Find profile by name
    profiles = await iterm2.PartialProfile.async_query(connection)
    target_profile = None

    for p in profiles:
        if p.name == name:
            target_profile = p
            break

    if not target_profile:
        handle_error(f"Profile '{name}' not found", 3)

    # Get full profile
    full_profile = await target_profile.async_get_full_profile()

    # Extract common properties
    profile_data = {
        "guid": full_profile.guid,
        "name": full_profile.name,
        "font": full_profile.normal_font,
        "font_size": full_profile.normal_font.size,
        "background_color": str(full_profile.background_color),
        "foreground_color": str(full_profile.foreground_color),
        "transparency": full_profile.transparency,
        "blur": full_profile.blur,
        "cursor_color": str(full_profile.cursor_color),
        "selection_color": str(full_profile.selection_color),
        "badge_text": full_profile.badge_text,
    }

    if as_json:
        click.echo(json.dumps(profile_data, indent=2))
    else:
        rprint(f"[bold]Profile: {full_profile.name}[/bold]")
        rprint(f"GUID: {full_profile.guid}")
        rprint(f"Font: {full_profile.normal_font.family} {full_profile.normal_font.size}pt")
        rprint(f"Background: {full_profile.background_color}")
        rprint(f"Foreground: {full_profile.foreground_color}")
        rprint(f"Transparency: {full_profile.transparency}")
        rprint(f"Blur: {full_profile.blur}")
        rprint(f"Cursor Color: {full_profile.cursor_color}")
        rprint(f"Selection Color: {full_profile.selection_color}")
        if full_profile.badge_text:
            rprint(f"Badge Text: {full_profile.badge_text}")


@profile.command()
@click.argument("name")
@click.option("--base", "-b", help="Base profile to copy from")
@run_command
async def create(
    name: str, base: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Create new profile."""
    # Get profiles
    profiles = await iterm2.PartialProfile.async_query(connection)

    # Check if profile already exists
    for p in profiles:
        if p.name == name:
            handle_error(f"Profile '{name}' already exists", 4)

    if base:
        # Find base profile
        base_profile = None
        for p in profiles:
            if p.name == base:
                base_profile = p
                break

        if not base_profile:
            handle_error(f"Base profile '{base}' not found", 3)

        # Get full base profile
        full_base = await base_profile.async_get_full_profile()

        # Create new profile based on base
        new_profile = await iterm2.Profile.async_create(connection, name, full_base.all_properties)
    else:
        # Create new profile with defaults
        new_profile = await iterm2.Profile.async_create(connection, name, {})

    if new_profile:
        click.echo(f"Created profile: {name}")
    else:
        handle_error("Failed to create profile")


@profile.command()
@click.argument("name")
@click.option("--session", "-s", help="Target session ID (default: active)")
@run_command
async def apply(
    name: str, session: Optional[str], connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Apply profile to current session."""
    # Find profile by name
    profiles = await iterm2.PartialProfile.async_query(connection)
    target_profile = None

    for p in profiles:
        if p.name == name:
            target_profile = p
            break

    if not target_profile:
        handle_error(f"Profile '{name}' not found", 3)

    # Get target session
    if session:
        target_session = app.get_session_by_id(session)
        if not target_session:
            handle_error(f"Session '{session}' not found", 3)
    else:
        # Use current session
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

        tab = window.current_tab
        if not tab:
            handle_error("No current tab", 3)

        target_session = tab.current_session
        if not target_session:
            handle_error("No current session", 3)

    # Apply profile
    await target_session.async_set_profile(target_profile)
    click.echo(f"Applied profile '{name}' to session")


@profile.command("set")
@click.argument("name")
@click.argument("property_name")
@click.argument("value")
@run_command
async def set_property(
    name: str, property_name: str, value: str, connection: iterm2.Connection, app: iterm2.App
) -> None:
    """Set profile property."""
    # Find profile by name
    profiles = await iterm2.PartialProfile.async_query(connection)
    target_profile = None

    for p in profiles:
        if p.name == name:
            target_profile = p
            break

    if not target_profile:
        handle_error(f"Profile '{name}' not found", 3)

    # Get full profile
    full_profile = await target_profile.async_get_full_profile()

    # Map common property names to actual properties
    property_map = {
        "font-size": lambda v: setattr(full_profile.normal_font, "size", float(v)),
        "font-family": lambda v: setattr(full_profile.normal_font, "family", v),
        "bg-color": lambda v: setattr(full_profile, "background_color", _parse_color(v)),
        "fg-color": lambda v: setattr(full_profile, "foreground_color", _parse_color(v)),
        "transparency": lambda v: setattr(full_profile, "transparency", float(v)),
        "blur": lambda v: setattr(full_profile, "blur", v.lower() == "true"),
        "cursor-color": lambda v: setattr(full_profile, "cursor_color", _parse_color(v)),
        "selection-color": lambda v: setattr(full_profile, "selection_color", _parse_color(v)),
        "badge-text": lambda v: setattr(full_profile, "badge_text", v),
    }

    if property_name in property_map:
        try:
            property_map[property_name](value)
            await full_profile.async_save()
            click.echo(f"Set {property_name} = {value} for profile '{name}'")
        except Exception as e:
            handle_error(f"Failed to set property: {e}", 4)
    else:
        handle_error(f"Unknown property: {property_name}", 4)


def _parse_color(color_str: str) -> iterm2.Color:
    """Parse color string to iterm2.Color."""
    # Remove # if present
    if color_str.startswith("#"):
        color_str = color_str[1:]

    # Parse hex color
    if len(color_str) == 6:
        r = int(color_str[0:2], 16) / 255.0
        g = int(color_str[2:4], 16) / 255.0
        b = int(color_str[4:6], 16) / 255.0
        return iterm2.Color(r, g, b)
    raise ValueError(f"Invalid color format: {color_str}")
