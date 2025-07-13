"""Configuration-related commands for iTerm2 CLI."""

import sys

import click
import iterm2

from ..core.connection import run_command
from ..core.errors import handle_error
from ..utils.config import Config


def register_config_commands(cli: click.Group) -> None:
    """Register configuration commands to the main CLI group."""

    config = Config()

    @cli.command("load")
    @click.argument("profile_name")
    @run_command
    async def load_profile(
        profile_name: str, connection: iterm2.Connection, app: iterm2.App
    ) -> None:
        """Load a custom profile from config file."""
        profile_steps = config.get_profile(profile_name)

        if not profile_steps:
            handle_error(f"Profile '{profile_name}' not found in config", 3)

        click.echo(f"Loading profile: {profile_name}")

        # Get current window and session
        window = app.current_terminal_window
        if not window:
            handle_error("No current window", 3)

        session = window.current_tab.current_session
        if not session:
            handle_error("No current session", 3)

        # Execute profile steps
        for step in profile_steps:
            if "command" in step:
                # Change directory or run command
                await session.async_send_text(step["command"] + "\r")
                click.echo(f"  Running: {step['command']}")

            elif "split" in step:
                # Split pane
                split_type = step["split"]
                if split_type == "vertical":
                    await session.async_split_pane(vertical=True)
                elif split_type == "horizontal":
                    await session.async_split_pane(vertical=False)
                elif split_type == "2x2":
                    # Create 2x2 grid
                    s1 = await session.async_split_pane(vertical=True)
                    await session.async_split_pane(vertical=False)
                    await s1.async_split_pane(vertical=False)
                else:
                    # Handle NxM grid (e.g., "3x2")
                    try:
                        cols, rows = map(int, split_type.split("x"))
                        # Create grid of sessions
                        sessions = [session]

                        # Create columns
                        for _ in range(cols - 1):
                            new_s = await sessions[0].async_split_pane(vertical=True)
                            sessions.insert(0, new_s)

                        # Create rows in each column
                        all_sessions = []
                        for s in sessions:
                            col_sessions = [s]
                            for _ in range(rows - 1):
                                new_s = await s.async_split_pane(vertical=False)
                                col_sessions.append(new_s)
                            all_sessions.extend(col_sessions)

                        sessions = all_sessions
                    except ValueError:
                        click.echo(f"  Warning: Invalid split format '{split_type}'")

                click.echo(f"  Split: {split_type}")

            # Handle pane-specific commands
            for i in range(1, 10):
                pane_key = f"pane{i}"
                if pane_key in step:
                    # Find the nth pane and run command
                    all_sessions = []
                    for tab in window.tabs:
                        all_sessions.extend(tab.sessions)

                    if i <= len(all_sessions):
                        target_session = all_sessions[i - 1]
                        await target_session.async_send_text(step[pane_key] + "\r")
                        click.echo(f"  Pane {i}: {step[pane_key]}")

        click.echo(f"Profile '{profile_name}' loaded successfully")

    @cli.command("alias")
    @click.argument("alias_name")
    @click.pass_context
    def run_alias(ctx: click.Context, alias_name: str) -> None:
        """Execute an alias from config file."""
        alias_command = config.get_alias(alias_name)

        if not alias_command:
            # Check if it's a built-in command
            all_aliases = config.get_all_aliases()
            if all_aliases:
                click.echo("Available aliases:")
                for name, cmd in all_aliases.items():
                    click.echo(f"  {name}: {cmd}")
            else:
                click.echo("No aliases defined in config file")
            sys.exit(3)

        click.echo(f"Running alias '{alias_name}': {alias_command}")

        # Parse and execute the alias command
        # Split command preserving quotes
        import shlex

        try:
            args = shlex.split(alias_command)
            if args and args[0] == "it2":
                args = args[1:]  # Remove 'it2' prefix if present

            # Create a new argument list for Click
            original_argv = sys.argv
            sys.argv = ["it2"] + args

            # Invoke the CLI with new arguments
            from ..cli import cli

            cli(standalone_mode=False)
        except Exception as e:
            handle_error(f"Failed to execute alias: {e}", 4)
        finally:
            sys.argv = original_argv

    @cli.command("config-path")
    def show_config_path() -> None:
        """Show configuration file path."""
        click.echo(f"Configuration file: {config.config_path}")
        if config.config_path.exists():
            click.echo("Status: File exists")
        else:
            click.echo("Status: File not found")
            click.echo(f"Create it with: touch {config.config_path}")

    @cli.command("config-reload")
    def reload_config() -> None:
        """Reload configuration file."""
        config.load()
        click.echo("Configuration reloaded")

        # Show summary
        profiles = config.get_all_profiles()
        aliases = config.get_all_aliases()

        if profiles:
            click.echo(f"Loaded {len(profiles)} profiles: {', '.join(profiles.keys())}")
        if aliases:
            click.echo(f"Loaded {len(aliases)} aliases: {', '.join(aliases.keys())}")
