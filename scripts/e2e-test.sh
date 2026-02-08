#!/bin/bash
# E2E test script for it2 CLI
#
# Runs side-effect commands against a live iTerm2 instance to verify
# that all CLI commands work correctly. Requires iTerm2 to be running
# with its Python API enabled.
#
# Usage:
#   ./scripts/e2e-test.sh                  # use 'it2' from PATH
#   ./scripts/e2e-test.sh /path/to/it2     # use specific binary
#
# The script creates a temporary window, exercises all commands inside it,
# and cleans up after itself. The only external side effect is that iTerm2
# may show a native "Close Window?" dialog when closing a window that has
# active processes — press OK to continue.

set -euo pipefail

IT2="${1:-it2}"
PASS=0
FAIL=0
FAILURES=""

run_test() {
  local name="$1"
  shift
  local output
  if output=$("$@" 2>&1); then
    echo "  PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $name"
    echo "    output: $output"
    FAIL=$((FAIL + 1))
    FAILURES="$FAILURES\n  - $name"
  fi
}

echo "=========================================="
echo "it2 E2E Tests"
echo "Binary: $IT2"
echo "$($IT2 --version 2>&1)"
echo "=========================================="

# ------------------------------------------------------------------
# App commands (read-only + activate)
# ------------------------------------------------------------------
echo ""
echo "[App]"
run_test "app activate" "$IT2" app activate
run_test "app version" "$IT2" app version
run_test "app theme (get)" "$IT2" app theme
run_test "app get-focus" "$IT2" app get-focus

# ------------------------------------------------------------------
# Create an isolated test window for the remaining tests
# ------------------------------------------------------------------
echo ""
echo "[Setup] Creating test window..."
WIN_OUTPUT=$("$IT2" window new 2>&1)
echo "  $WIN_OUTPUT"
sleep 0.5

NEW_WIN=$("$IT2" window list --json 2>&1 | python3 -c "
import sys, json
wins = json.load(sys.stdin)
print(wins[-1]['id'])
")
echo "  Window ID: ${NEW_WIN:0:40}..."

# ------------------------------------------------------------------
# Window commands (side effects)
# ------------------------------------------------------------------
echo ""
echo "[Window]"
run_test "window list" "$IT2" window list
run_test "window list --json" "$IT2" window list --json
run_test "window move" "$IT2" window move 200 200 "$NEW_WIN"
run_test "window resize" "$IT2" window resize 900 600 "$NEW_WIN"
run_test "window fullscreen on" "$IT2" window fullscreen toggle "$NEW_WIN"
sleep 0.5
run_test "window fullscreen off" "$IT2" window fullscreen toggle "$NEW_WIN"
sleep 0.5

# ------------------------------------------------------------------
# Tab commands (side effects)
# ------------------------------------------------------------------
echo ""
echo "[Tab]"
run_test "tab list" "$IT2" tab list
run_test "tab list --json" "$IT2" tab list --json
run_test "tab new" "$IT2" tab new --window "$NEW_WIN"
sleep 0.3
run_test "tab next" "$IT2" tab next
sleep 0.2
run_test "tab prev" "$IT2" tab prev
sleep 0.2
run_test "tab goto 0" "$IT2" tab goto 0
sleep 0.2

# ------------------------------------------------------------------
# Session commands (side effects)
# ------------------------------------------------------------------
echo ""
echo "[Session]"
run_test "session list" "$IT2" session list
run_test "session list --json" "$IT2" session list --json
run_test "session split (horizontal)" "$IT2" session split
sleep 0.3
run_test "session split --vertical" "$IT2" session split --vertical
sleep 0.3

# Pick a session in the test window
SESSION_ID=$("$IT2" session list --json 2>&1 | python3 -c "
import sys, json
sessions = json.load(sys.stdin)
print(sessions[-1]['id'])
")
echo "  Target session: ${SESSION_ID:0:20}..."

run_test "session set-name" "$IT2" session set-name "e2e-test" --session "$SESSION_ID"
run_test "session send" "$IT2" session send "echo hello" --session "$SESSION_ID"
run_test "session run" "$IT2" session run "echo test" --session "$SESSION_ID"
sleep 0.3
run_test "session read" "$IT2" session read --session "$SESSION_ID"
run_test "session get-var" "$IT2" session get-var columns --session "$SESSION_ID"
run_test "session clear" "$IT2" session clear --session "$SESSION_ID"

# ------------------------------------------------------------------
# Profile commands
# ------------------------------------------------------------------
echo ""
echo "[Profile]"
run_test "profile list" "$IT2" profile list
run_test "profile show Default" "$IT2" profile show Default
run_test "profile apply" "$IT2" profile apply Default --session "$SESSION_ID"

# ------------------------------------------------------------------
# Broadcast commands
# ------------------------------------------------------------------
echo ""
echo "[Broadcast]"
run_test "broadcast on" "$IT2" app broadcast on
run_test "broadcast off" "$IT2" app broadcast off

# ------------------------------------------------------------------
# Shortcuts
# ------------------------------------------------------------------
echo ""
echo "[Shortcuts]"
run_test "ls" "$IT2" ls
run_test "ls --json" "$IT2" ls --json

# ------------------------------------------------------------------
# Config commands (no iTerm2 connection needed)
# ------------------------------------------------------------------
echo ""
echo "[Config]"
run_test "config-path" "$IT2" config-path
run_test "config-reload" "$IT2" config-reload

# ------------------------------------------------------------------
# Cleanup: close the extra tab, then the test window
# ------------------------------------------------------------------
echo ""
echo "[Cleanup]"

EXTRA_TAB=$("$IT2" tab list --json 2>&1 | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
win = '$NEW_WIN'
wintabs = [t for t in tabs if t.get('window_id') == win]
if len(wintabs) > 1:
    print(wintabs[-1]['id'])
else:
    print('')
")
if [ -n "$EXTRA_TAB" ]; then
  run_test "tab close" "$IT2" tab close "$EXTRA_TAB" --force
fi

run_test "window close" "$IT2" window close "$NEW_WIN" --force

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  echo -e "Failures:$FAILURES"
  echo "=========================================="
  exit 1
else
  echo "=========================================="
  exit 0
fi
