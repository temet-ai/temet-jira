"""Map Jira status categories to Rich markup styles."""

_CATEGORY_STYLES = {
    "new": "status.todo",
    "indeterminate": "status.inprogress",
    "done": "status.done",
    "undefined": "muted",
}

_STATUS_BLOCKED = {"blocked", "impediment", "on hold"}


def status_style(status_name: str, category_key: str | None = None) -> str:
    """Return a Rich style name for a Jira status."""
    if status_name.lower() in _STATUS_BLOCKED:
        return "status.blocked"
    if category_key:
        return _CATEGORY_STYLES.get(category_key.lower(), "muted")
    # best-effort fallback from name
    low = status_name.lower()
    if "progress" in low or "review" in low or "doing" in low:
        return "status.inprogress"
    if "done" in low or "closed" in low or "resolved" in low:
        return "status.done"
    return "status.todo"


def format_status(status_name: str, category_key: str | None = None) -> str:
    """Return Rich markup string for a status label."""
    style = status_style(status_name, category_key)
    return f"[{style}]{status_name}[/{style}]"
