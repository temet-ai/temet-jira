"""Pure formatting functions for Jira field values."""

from datetime import datetime
from typing import Any


def format_date(date_str: str | None) -> str:
    """Format ISO date string for full display (YYYY-MM-DD HH:MM)."""
    if not date_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return date_str


def format_date_relative(date_str: str | None) -> str:
    """Format ISO date string as relative time (e.g., '5m ago', 'Yesterday')."""
    if not date_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            else:
                return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return date_str[:10] if len(date_str) >= 10 else date_str


def get_priority(fields: dict[str, Any]) -> str:
    """Extract priority display value from issue fields."""
    priority = fields.get("priority")
    if priority:
        name = priority.get("name", "Not set")
        return str(name) if name else "Not set"
    return "Not set"


def get_user_display(user: dict[str, Any] | None) -> str:
    """Extract user display name from user dict."""
    if not user:
        return "Unassigned"
    if not isinstance(user, dict) or not user:
        return "Unknown"
    display = user.get("displayName", user.get("emailAddress", "Unknown"))
    return str(display) if display else "Unknown"


def truncate_summary(summary: str, max_length: int = 50) -> str:
    """Truncate summary text with ellipsis if too long."""
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 3] + "..."
