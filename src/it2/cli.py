"""Main CLI entry point for iTerm2 CLI."""

import click

from . import __version__
from .commands import app, monitor, profile, session, tab, window
from .commands.config_commands import register_config_commands
from .commands.shortcuts import register_shortcuts


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="it2")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """iTerm2 CLI - Control iTerm2 from the command line.

    A powerful command-line interface for controlling iTerm2 using its Python API.

    Examples:
        \b
        # Send text to current session
        it2 session send "Hello, World!"

        # Run command in all sessions
        it2 session run "ls -la" --all

        # Split current session vertically
        it2 session split --vertical

        # Create new window with specific profile
        it2 window new --profile "Development"
    """
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register command groups
cli.add_command(session.session)
cli.add_command(window.window)
cli.add_command(tab.tab)
cli.add_command(profile.profile)
cli.add_command(app.app)
cli.add_command(monitor.monitor)

# Register shortcuts
register_shortcuts(cli)

# Register config commands
register_config_commands(cli)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
