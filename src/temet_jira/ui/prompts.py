"""Interactive prompts with automatic TTY fallback.

In interactive mode (TTY): arrow-key navigation via questionary.
In non-interactive mode (pipes, CI, --no-interactive): numbered prompts via click.
"""

import click

from .console import is_interactive

try:
    import questionary
    from questionary import Style as QStyle

    _STYLE = QStyle([
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("separator", "fg:gray"),
        ("instruction", "fg:gray dim"),
    ])
    _HAS_QUESTIONARY = True
except ImportError:
    _HAS_QUESTIONARY = False


def select(message: str, choices: list[str], default: str | None = None) -> str | None:
    """Single arrow-key select; falls back to numbered prompt."""
    if _HAS_QUESTIONARY and is_interactive():
        return questionary.select(message, choices=choices, default=default, style=_STYLE).ask()
    return _numbered_fallback(message, choices, default, allow_skip=False)


def select_optional(message: str, choices: list[str]) -> str | None:
    """Single select where 0/skip returns None."""
    if _HAS_QUESTIONARY and is_interactive():
        result = questionary.select(
            message, choices=["(skip)"] + choices, style=_STYLE
        ).ask()
        return None if result == "(skip)" else result
    return _numbered_fallback(message, choices, default=None, allow_skip=True)


def checkbox(message: str, choices: list[str]) -> list[str]:
    """Multi-select checkboxes; falls back to iterative numbered prompt."""
    if _HAS_QUESTIONARY and is_interactive():
        result = questionary.checkbox(message, choices=choices, style=_STYLE).ask()
        return result or []
    return _numbered_multi_fallback(message, choices)


def confirm(message: str, default: bool = True) -> bool:
    """Yes/no confirmation; falls back to click.confirm."""
    if _HAS_QUESTIONARY and is_interactive():
        result = questionary.confirm(message, default=default, style=_STYLE).ask()
        return result if result is not None else default
    return click.confirm(message, default=default)


def text(message: str, default: str = "", password: bool = False) -> str:
    """Free text input; falls back to click.prompt."""
    if _HAS_QUESTIONARY and is_interactive() and not password:
        result = questionary.text(message, default=default, style=_STYLE).ask()
        return result or default
    return click.prompt(message, default=default or None, hide_input=password) or ""


# ---------------------------------------------------------------------------
# Non-interactive fallbacks
# ---------------------------------------------------------------------------

def _numbered_fallback(
    message: str, choices: list[str], default: str | None, allow_skip: bool
) -> str | None:
    click.echo(f"\n{message}")
    for i, c in enumerate(choices, 1):
        click.echo(f"  {i}. {c}")
    if allow_skip:
        click.echo("  0. skip")
    prompt_default = 0 if allow_skip else 1
    while True:
        raw = click.prompt("Choice", default=str(prompt_default))
        try:
            idx = int(raw)
            if allow_skip and idx == 0:
                return None
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        except ValueError:
            # treat as literal value
            if raw in choices:
                return raw
        click.echo(f"  Enter a number 1–{len(choices)}" + (" or 0 to skip" if allow_skip else ""))


def _numbered_multi_fallback(message: str, choices: list[str]) -> list[str]:
    selected: list[str] = []
    remaining = list(choices)
    click.echo(f"\n{message} (enter numbers one at a time, 0 when done)")
    while remaining:
        for i, c in enumerate(remaining, 1):
            click.echo(f"  {i}. {c}")
        click.echo("  0. done")
        raw = click.prompt("Add", default="0")
        try:
            idx = int(raw)
            if idx == 0:
                break
            if 1 <= idx <= len(remaining):
                selected.append(remaining.pop(idx - 1))
        except ValueError:
            if raw and raw not in selected:
                selected.append(raw)
            break
    return selected
