from rich.theme import Theme

THEME = Theme({
    "key": "bold cyan",          # Issue keys (PROJ-123), IDs
    "success": "bold green",     # ✓ confirmations
    "warning": "bold yellow",    # ⚠ warnings
    "error": "bold red",         # ✗ errors
    "info": "bold blue",         # ℹ informational
    "accent": "magenta",         # Sprint names, epic names
    "muted": "dim",              # Timestamps, secondary metadata
    "header": "bold",            # Table headers
    "status.todo": "blue",       # Jira status category: To Do
    "status.inprogress": "yellow", # In Progress
    "status.done": "green",      # Done
    "status.blocked": "bold red",# Blocked
})
