import os
import sys

from rich.console import Console

from .theme import THEME


def is_interactive() -> bool:
    """True when stdin+stdout are TTYs and no CI/automation env vars set."""
    if os.environ.get("CI") or os.environ.get("JIRA_NO_INTERACTIVE") or os.environ.get("NO_INTERACTIVE"):
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def _build_console(stderr: bool = False) -> Console:
    no_color = "NO_COLOR" in os.environ
    force_color = "FORCE_COLOR" in os.environ
    return Console(
        theme=THEME,
        stderr=stderr,
        no_color=no_color,
        force_terminal=True if force_color else None,
    )


console = _build_console(stderr=False)      # all output
err_console = _build_console(stderr=True)   # spinners, progress, warnings
