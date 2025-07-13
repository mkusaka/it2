# Test Coverage Summary for Tab Commands

This document summarizes the test coverage for the tab commands in `/tests/test_tab_commands.py`.

## Test Structure

The test file follows the same pattern as other command test files:
- Uses `setup_iterm2_mocks` helper function for mock setup
- Creates appropriate fixtures (`mock_tab`, `mock_window`, `mock_app`)
- Tests both success and error cases
- Includes JSON output tests where applicable

## Commands Tested

### 1. Tab Creation (`tab new`)
- ✅ Basic tab creation
- ✅ Tab creation with profile
- ✅ Tab creation with command to run
- ✅ Tab creation in specific window
- ✅ Window not found error
- ✅ No current window error
- ✅ Tab creation failure

### 2. Tab Listing (`tab list`)
- ✅ JSON output format
- ✅ Listing tabs from specific window
- ✅ Window not found error
- ⏭️ Table output (skipped - Rich console formatting difficult to test)

### 3. Tab Closing (`tab close`)
- ✅ Close current tab
- ✅ Close specific tab by ID
- ✅ Tab not found error
- ✅ No current window error
- ✅ No current tab error

### 4. Tab Selection (`tab select`)
- ✅ Select by tab ID
- ✅ Select by index
- ✅ Index out of range error
- ✅ Select by index with specific window
- ✅ Tab not found error

### 5. Tab Moving (`tab move`)
- ✅ Move current tab
- ✅ Move specific tab
- ✅ Tab not found error
- ✅ No current window error
- ✅ No current tab error

### 6. Tab Navigation (`tab next`, `tab prev`)
- ✅ Next tab navigation
- ✅ Next tab wrap-around
- ✅ Previous tab navigation
- ✅ Previous tab wrap-around
- ✅ No current window error
- ✅ No current tab error

### 7. Tab Goto (`tab goto`)
- ✅ Go to tab by index
- ✅ Go to tab with specific window
- ✅ Window not found error
- ✅ No current window error
- ✅ Index out of range error

### 8. Error Handling
- ✅ Command without iTerm2 cookie

## Test Count

- Total tests: 47
- Skipped tests: 1 (Rich console table formatting)
- All major functionality is covered

## Mock Objects Used

1. **mock_tab**: Simulates iTerm2 tab object with:
   - `tab_id`
   - `async_select()`
   - `async_close()`
   - `async_move_to_window_index()`
   - `sessions` and `current_session`

2. **mock_window**: Simulates iTerm2 window object with:
   - `window_id`
   - `tabs` list
   - `current_tab`
   - `async_create_tab()`

3. **mock_app**: Simulates iTerm2 app object with:
   - `windows` list
   - `current_terminal_window`

## Notes

- The tests focus on command execution and error handling
- Complex iTerm2 objects are mocked to avoid dependency on actual iTerm2 environment
- The test patterns are consistent with existing test files in the project
- All exit codes are properly tested (0 for success, 1-4 for various errors)