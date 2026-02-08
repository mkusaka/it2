# E2E Testing Guide

This document describes how to run end-to-end tests for the `it2` CLI against a live iTerm2 instance.

## Prerequisites

- **macOS** with iTerm2 running
- iTerm2's **Python API** enabled (Preferences → General → Magic → Enable Python API)
- Python 3.10+ installed (tests should cover all versions in the CI matrix)

## Unit Tests vs E2E Tests

| | Unit tests (`pytest`) | E2E tests (`e2e-test.sh`) |
|---|---|---|
| **Runs in CI** | Yes | No (requires live iTerm2) |
| **iTerm2 connection** | Mocked | Real |
| **Side effects** | None | Creates/closes windows, tabs, sessions |
| **Speed** | ~1 second | ~10 seconds per Python version |
| **Purpose** | Logic correctness | Verify real iTerm2 API interaction |

## Quick Start

```bash
# Run with the default it2 from PATH
./scripts/e2e-test.sh

# Run with a specific binary
./scripts/e2e-test.sh /path/to/venv/bin/it2
```

## Testing Across Multiple Python Versions

Use `uv` to create isolated venvs for each target version:

```bash
VERSIONS="3.10 3.11 3.12 3.13 3.14"

for v in $VERSIONS; do
  uv venv --python "$v" "/tmp/it2-test-$v"
  uv pip install --python "/tmp/it2-test-$v/bin/python" -e ".[dev]"
done

for v in $VERSIONS; do
  echo ""
  echo "====== Python $v ======"
  ./scripts/e2e-test.sh "/tmp/it2-test-$v/bin/it2"
done

# Cleanup
for v in $VERSIONS; do
  rm -rf "/tmp/it2-test-$v"
done
```

## What the Script Tests

The script creates a temporary window, runs every command group inside it, and tears it down at the end.

### App commands
- `app activate` — bring iTerm2 to front
- `app version` — query iTerm2 version
- `app theme` — get current theme
- `app get-focus` — get focused window/tab/session

### Window commands (side effects)
- `window list` / `window list --json`
- `window new` — creates a test window (cleaned up at the end)
- `window move` — repositions the test window
- `window resize` — resizes the test window
- `window fullscreen toggle` — toggles fullscreen on then off
- `window close --force` — closes the test window

### Tab commands (side effects)
- `tab list` / `tab list --json`
- `tab new` — creates a tab in the test window
- `tab next` / `tab prev` / `tab goto`
- `tab close --force`

### Session commands (side effects)
- `session list` / `session list --json`
- `session split` (horizontal) / `session split --vertical`
- `session set-name` — renames a session
- `session send` — sends text without newline
- `session run` — sends text with newline (executes as command)
- `session read` — reads screen contents
- `session get-var` — reads a session variable
- `session clear` — clears the screen

### Profile commands
- `profile list` / `profile show Default`
- `profile apply` — applies a profile to a session

### Broadcast commands
- `app broadcast on` / `app broadcast off`

### Shortcuts
- `ls` (alias for `session list`)
- `ls --json`

### Config commands
- `config-path` — shows config file path
- `config-reload` — reloads config file

## Known Behaviors

### iTerm2 native "Close Window?" dialog

When closing a window that contains sessions with active processes, iTerm2 may show a native macOS confirmation dialog:

> Close Window #N?

This is **not** a bug. The `--force` flag in `window close` and `tab close` skips the CLI-level confirmation (`click.confirm()`), but it does **not** suppress iTerm2's own native dialog. You need to click "OK" manually.

This happens because the E2E test runs `session run "echo test"` which spawns a shell process. When the window is closed shortly after, iTerm2 detects the active process and asks for confirmation.

**Workaround when running tests**: just press OK/Enter when the dialog appears.

### Commands NOT tested by the script

The following commands are intentionally excluded from automated E2E testing:

| Command | Reason |
|---|---|
| `app quit` | Would terminate iTerm2 |
| `app theme <value>` (set) | Changes user's theme preference |
| `app broadcast add` | Requires specific session IDs setup |
| `session close` | Tested implicitly via `window close` |
| `session restart` | Restarts the shell process |
| `session copy` | Depends on selection state |
| `session capture` | Writes files to disk |
| `session set-var` | May affect session behavior |
| `profile set` | Modifies profile permanently |
| `window arrange-*` | Modifies saved arrangements |
| `monitor *` | Long-running / blocking commands |
| `load` / `alias` | Requires config file setup |
| Shortcuts: `new`, `newtab`, `send`, `run`, `split`, `vsplit`, `clear` | Covered by their non-shortcut equivalents |

## Adding New Commands

When adding a new command to `it2`, add a corresponding `run_test` call to `scripts/e2e-test.sh`. Place it in the appropriate section and ensure cleanup if the command creates resources.
