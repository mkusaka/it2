"""Error handling for iTerm2 CLI."""

import sys
from typing import NoReturn


class IT2Error(Exception):
    """Base exception for IT2 CLI errors."""

    exit_code = 1


class IT2ConnectionError(IT2Error):
    """Connection-related errors."""

    exit_code = 2


class TargetNotFoundError(IT2Error):
    """Target (session/window/tab) not found errors."""

    exit_code = 3


class InvalidArgumentsError(IT2Error):
    """Invalid arguments errors."""

    exit_code = 4


def handle_error(message: str, exit_code: int = 1) -> NoReturn:
    """Print error message and exit with given code."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def handle_connection_error() -> NoReturn:
    """Handle connection errors with helpful message."""
    print("Error: Failed to connect to iTerm2", file=sys.stderr)
    print("Make sure:", file=sys.stderr)
    print("  1. iTerm2 is running", file=sys.stderr)
    print(
        "  2. Python API is enabled (Preferences > General > Magic > Enable Python API)",
        file=sys.stderr,
    )
    print("  3. You're running this command from within iTerm2", file=sys.stderr)
    sys.exit(2)
