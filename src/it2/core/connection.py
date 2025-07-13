"""Connection management for iTerm2 API."""

import os
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

import iterm2
from iterm2 import App, Connection

T = TypeVar("T")


class ConnectionManager:
    """Manages the connection to iTerm2."""

    def __init__(self) -> None:
        self._connection: Optional[Connection] = None
        self._app: Optional[App] = None

    async def connect(self) -> Connection:
        """Establish connection to iTerm2."""
        if not self._connection:
            self._connection = await iterm2.Connection.async_create()
            self._app = await iterm2.async_get_app(self._connection)
        return self._connection

    async def get_app(self) -> App:
        """Get the iTerm2 app instance."""
        if not self._app:
            await self.connect()
        return self._app

    async def close(self) -> None:
        """Close the connection."""
        if self._connection:
            await self._connection.async_close()
            self._connection = None
            self._app = None


# Global connection manager instance
_connection_manager = ConnectionManager()


def with_connection(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to ensure connection is established before running command."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            connection = await _connection_manager.connect()
            app = await _connection_manager.get_app()
            # Inject connection and app into function kwargs
            kwargs["connection"] = connection
            kwargs["app"] = app
            return await func(*args, **kwargs)
        except iterm2.RPCException as e:
            print(f"iTerm2 API error: {e}", file=sys.stderr)
            sys.exit(3)
        except Exception as e:
            print(f"Connection error: {e}", file=sys.stderr)
            print("Make sure iTerm2 is running and Python API is enabled.", file=sys.stderr)
            print("(Preferences > General > Magic > Enable Python API)", file=sys.stderr)
            sys.exit(2)
        finally:
            await _connection_manager.close()

    return wrapper


def run_command(func: Callable[..., Awaitable[T]]) -> Any:
    """Run an async command function with connection management."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Try external connection first (like iterm2-focus), fallback to internal
        import asyncio

        async def run_with_connection() -> Any:
            connection = None
            try:
                connection = await iterm2.Connection.async_create()
                app = await iterm2.async_get_app(connection)
                # Inject connection and app into function kwargs
                kwargs["connection"] = connection
                kwargs["app"] = app
                return await func(*args, **kwargs)
            finally:
                # Connection objects don't have async_close(), they close automatically
                pass

        try:
            # Use asyncio.run for external connection
            return asyncio.run(run_with_connection())
        except Exception:
            # If external connection fails and we have ITERM2_COOKIE, try internal
            if os.environ.get("ITERM2_COOKIE"):
                try:
                    return iterm2.run_until_complete(func(*args, **kwargs))
                except Exception:
                    # Both failed, show error
                    print(
                        "Error: Not running inside iTerm2 or Python API not enabled.",
                        file=sys.stderr,
                    )
                    print(
                        "Enable Python API in: Preferences > General > Magic > Enable Python API",
                        file=sys.stderr,
                    )
                    sys.exit(2)
            else:
                # No cookie and external failed, show error
                print(
                    "Error: Not running inside iTerm2 or Python API not enabled.", file=sys.stderr
                )
                print(
                    "Enable Python API in: Preferences > General > Magic > Enable Python API",
                    file=sys.stderr,
                )
                sys.exit(2)

    return wrapper
