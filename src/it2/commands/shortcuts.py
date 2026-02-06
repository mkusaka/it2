"""Shortcuts and aliases for common commands."""

import click


def register_shortcuts(cli: click.Group) -> None:
    """Register shortcut commands to the main CLI group."""

    # Session shortcuts
    @cli.command("send")
    @click.argument("text")
    @click.option("--session", "-s", help="Target session ID (default: active)")
    @click.option("--all", "-a", "all_sessions", is_flag=True, help="Send to all sessions")
    @click.pass_context
    def send_shortcut(ctx: click.Context, text: str, session: str, all_sessions: bool) -> None:
        """Shortcut for 'it2 session send'."""
        from . import session as session_module

        ctx.invoke(session_module.send, text=text, session=session, all_sessions=all_sessions)

    @cli.command("run")
    @click.argument("command")
    @click.option("--session", "-s", help="Target session ID (default: active)")
    @click.option("--all", "-a", "all_sessions", is_flag=True, help="Run in all sessions")
    @click.pass_context
    def run_shortcut(ctx: click.Context, command: str, session: str, all_sessions: bool) -> None:
        """Shortcut for 'it2 session run'."""
        from . import session as session_module

        ctx.invoke(
            session_module.run, command=command, session=session, all_sessions=all_sessions
        )

    @cli.command("split")
    @click.option("--vertical", "-v", is_flag=True, help="Split vertically")
    @click.option("--session", "-s", help="Target session ID (default: active)")
    @click.option("--profile", "-p", help="Profile to use for new pane")
    @click.pass_context
    def split_shortcut(ctx: click.Context, vertical: bool, session: str, profile: str) -> None:
        """Shortcut for 'it2 session split'."""
        from . import session as session_module

        ctx.invoke(session_module.split, vertical=vertical, session=session, profile=profile)

    @cli.command("vsplit")
    @click.option("--session", "-s", help="Target session ID (default: active)")
    @click.option("--profile", "-p", help="Profile to use for new pane")
    @click.pass_context
    def vsplit_shortcut(ctx: click.Context, session: str, profile: str) -> None:
        """Shortcut for 'it2 session split --vertical'."""
        from . import session as session_module

        ctx.invoke(session_module.split, vertical=True, session=session, profile=profile)

    @cli.command("clear")
    @click.option("--session", "-s", help="Target session ID (default: active)")
    @click.pass_context
    def clear_shortcut(ctx: click.Context, session: str) -> None:
        """Shortcut for 'it2 session clear'."""
        from . import session as session_module

        ctx.invoke(session_module.clear, session=session)

    @cli.command("ls")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    @click.pass_context
    def ls_shortcut(ctx: click.Context, as_json: bool) -> None:
        """Shortcut for 'it2 session list'."""
        from . import session as session_module

        ctx.invoke(session_module.list_sessions, as_json=as_json)

    # Window shortcuts
    @cli.command("new")
    @click.option("--profile", "-p", help="Profile to use for new window")
    @click.option("--command", "-c", help="Command to run in new window")
    @click.pass_context
    def new_shortcut(ctx: click.Context, profile: str, command: str) -> None:
        """Shortcut for 'it2 window new'."""
        from . import window as window_module

        ctx.invoke(window_module.new, profile=profile, command=command)

    # Tab shortcut - use a different name to avoid conflict with tab group
    @cli.command("newtab")
    @click.option("--profile", "-p", help="Profile to use for new tab")
    @click.option("--window", "-w", help="Window ID to create tab in (default: current)")
    @click.option("--command", "-c", help="Command to run in new tab")
    @click.pass_context
    def newtab_shortcut(ctx: click.Context, profile: str, window: str, command: str) -> None:
        """Shortcut for 'it2 tab new'."""
        from . import tab as tab_module

        ctx.invoke(tab_module.new, profile=profile, window=window, command=command)
