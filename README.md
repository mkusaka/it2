# it2

A powerful command-line interface for controlling iTerm2 using its Python API.

## Features

- **Session Management**: Send text, execute commands, split panes, manage sessions
- **Window Control**: Create, move, resize, and manage windows
- **Tab Operations**: Create and navigate between tabs
- **Profile Management**: List, show, and apply iTerm2 profiles
- **Broadcasting**: Send input to multiple sessions simultaneously
- **Monitoring**: Watch session output, keystrokes, and variables in real-time
- **Configuration**: Define custom profiles and aliases in YAML
- **Shortcuts**: Quick access to common commands

## Requirements

- macOS with iTerm2 3.3.0 or later
- Python 3.10+
- iTerm2 Python API enabled (Preferences > General > Magic > Enable Python API)

## Installation

### Using pip

```bash
pip install it2
```

### Using uv (recommended)

```bash
uv tool install it2
```

## Quick Start

```bash
# Send text to current session
it2 send "Hello, World!"

# Run a command
it2 run "ls -la"

# Split the current pane vertically
it2 vsplit

# Create a new window
it2 new

# List all sessions
it2 ls
```

## Basic Usage

### Session Operations

```bash
# Send text (without newline)
it2 session send "text"
it2 send "text"  # shortcut

# Execute command (with newline)
it2 session run "command"
it2 run "command"  # shortcut

# Target specific session or all sessions
it2 send "text" --session <id>
it2 send "text" --all

# Split panes
it2 session split          # horizontal split
it2 session split -v       # vertical split
it2 vsplit                 # shortcut for vertical split

# Session management
it2 session list           # list all sessions
it2 session close          # close current session
it2 session restart        # restart session
it2 session clear          # clear screen
```

### Window Operations

```bash
# Window management
it2 window new             # create new window
it2 window list            # list all windows
it2 window close           # close current window
it2 window focus <id>      # focus specific window

# Window manipulation
it2 window move 100 200    # move to position
it2 window resize 800 600  # resize window
it2 window fullscreen on   # enable fullscreen

# Window arrangements
it2 window arrange save "dev"      # save arrangement
it2 window arrange restore "dev"   # restore arrangement
```

### Tab Operations

```bash
# Tab management
it2 tab new                # create new tab
it2 tab list               # list all tabs
it2 tab close              # close current tab
it2 tab select <id>        # select specific tab

# Tab navigation
it2 tab next               # go to next tab
it2 tab prev               # go to previous tab
it2 tab goto 2             # go to tab by index
```

### Profile Operations

```bash
# Profile management
it2 profile list           # list all profiles
it2 profile show "Default" # show profile details
it2 profile apply "MyProfile"

# Profile configuration
it2 profile set "MyProfile" font-size 14
it2 profile set "MyProfile" bg-color "#000000"
it2 profile set "MyProfile" transparency 0.9
```

### Application Control

```bash
# App management
it2 app activate           # bring iTerm2 to front
it2 app hide               # hide iTerm2
it2 app version            # show iTerm2 version
it2 app theme              # show current theme
it2 app theme dark         # set theme (light, dark, light-hc, dark-hc, automatic, minimal)

# Broadcasting
it2 app broadcast on       # enable broadcasting
it2 app broadcast off      # disable broadcasting
it2 app broadcast add session1 session2  # create broadcast group
```

### Monitoring

```bash
# Monitor output
it2 monitor output -f                      # follow output
it2 monitor output -f -p "ERROR"           # filter by pattern

# Monitor keystrokes
it2 monitor keystroke                      # all keystrokes
it2 monitor keystroke -p "^[a-z]+$"        # filter by regex

# Monitor variables
it2 monitor variable lastCommand           # session variable
it2 monitor variable effectiveTheme --app  # app variable

# Monitor prompts (requires shell integration)
it2 monitor prompt
```

## Configuration

Create `~/.it2rc.yaml` to define custom profiles and aliases:

```yaml
# Custom profiles
profiles:
  dev:
    - command: cd ~/project
    - split: vertical
    - pane1: npm run dev
    - pane2: npm test --watch
  
  servers:
    - split: 2x2
    - pane1: ssh server1
    - pane2: ssh server2
    - pane3: ssh server3
    - pane4: ssh server4

# Command aliases
aliases:
  deploy: session run "deploy.sh" --all
  logs: monitor output -f -p "ERROR|WARN"
  dev-setup: load dev
```

Use configurations:

```bash
# Load a profile
it2 load dev

# Execute an alias
it2 alias deploy

# Show config path
it2 config-path

# Reload configuration
it2 config-reload
```

## Advanced Examples

### Development Environment Setup

```bash
# Create a development workspace
it2 window new --profile "Development"
it2 split
it2 send "cd ~/project && npm run dev"
it2 session focus 2
it2 send "cd ~/project && npm test --watch"
```

### Multi-Server Management

```bash
# SSH to multiple servers with broadcasting
it2 tab new
it2 split && it2 split && it2 split
it2 app broadcast on
it2 send "ssh production-server"
```

### Automated Deployment

Create a deployment script:

```bash
#!/bin/bash
# deploy.sh

# Create deployment window
it2 window new --profile "Deploy"

# Split for monitoring
it2 split -v

# Start deployment in first pane
it2 send "cd ~/project && ./deploy-prod.sh"

# Monitor logs in second pane
it2 session focus 2
it2 run "tail -f /var/log/deploy.log"

# Watch for errors
it2 monitor output -f -p "ERROR|FAILED"
```

## Environment Variables

- `IT2_DEFAULT_PROFILE`: Default profile name
- `IT2_CONFIG_PATH`: Path to configuration file (default: `~/.it2rc.yaml`)
- `IT2_TIMEOUT`: Command timeout in seconds

## Error Codes

- `0`: Success
- `1`: General error
- `2`: Connection error (iTerm2 not running or API not enabled)
- `3`: Target not found (session/window/tab not found)
- `4`: Invalid arguments

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/mkusaka/it2.git
cd it2

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy .
```

### Project Structure

```
it2/
├── src/
│   └── it2/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── commands/           # Command modules
│       │   ├── session.py
│       │   ├── window.py
│       │   ├── tab.py
│       │   ├── profile.py
│       │   ├── app.py
│       │   ├── monitor.py
│       │   ├── shortcuts.py
│       │   └── config_commands.py
│       ├── core/               # Core functionality
│       │   ├── connection.py
│       │   ├── session_handler.py
│       │   └── errors.py
│       └── utils/              # Utilities
│           └── config.py
├── tests/                      # Test files
├── pyproject.toml              # Project configuration
├── README.md                   # This file
└── example.it2rc.yaml          # Example configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

GPLv2+ License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built on the [iTerm2 Python API](https://iterm2.com/python-api/)
- Inspired by tmux and screen command-line interfaces
- Uses [Click](https://click.palletsprojects.com/) for CLI framework
