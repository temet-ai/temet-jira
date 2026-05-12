"""Jira display formatters for terminal output.

This module provides backward-compatible re-exports from the refactored
document.display and document.adf submodules.

For new code, prefer importing directly from:
- `temet_jira.document.display` for Rich terminal formatting
- `temet_jira.document.adf` for ADF text extraction
- `temet_jira.document` for ADF document building
"""

from typing import Any

# Re-export ADF extractor
from temet_jira.document.adf import extract_text_from_adf

# Re-export document builders for backward compatibility
from temet_jira.document.builders import (
    DocumentBuilder,
    EpicBuilder,
    IssueBuilder,
    SubtaskBuilder,
)

# Re-export display functions
from temet_jira.document.display import (
    IssuePanelBuilder,
    IssueTableBuilder,
    ProjectTableBuilder,
    TransitionTableBuilder,
    format_date,
    format_date_relative,
    format_issue,
    format_issues_table,
    format_projects_table,
    format_transitions_table,
    get_priority,
    get_user_display,
)

# Backward compatibility aliases
JiraDocumentBuilder = DocumentBuilder
_format_date_short = format_date_relative


class JiraFormatter:
    """Backward-compatible formatter class.

    All methods delegate to standalone functions in document.display.
    For new code, use the standalone functions directly.
    """

    @staticmethod
    def format_issue(issue: dict[str, Any]) -> None:
        """Format and display a single Jira issue."""
        format_issue(issue)

    @staticmethod
    def format_issues_table(
        issues: list[dict[str, Any]],
        title: str = "Jira Issues",  # noqa: ARG004
    ) -> None:
        """Format multiple issues as a table."""
        format_issues_table(issues)

    @staticmethod
    def format_projects_table(projects: list[dict[str, Any]]) -> None:
        """Format projects as a table."""
        format_projects_table(projects)

    @staticmethod
    def format_transitions_table(transitions: list[dict[str, Any]]) -> None:
        """Format issue transitions as a table."""
        format_transitions_table(transitions)

    @staticmethod
    def _extract_text_from_adf(content: str | dict[str, Any]) -> str:
        """Extract plain text from ADF content."""
        return extract_text_from_adf(content)

    @staticmethod
    def _get_priority(fields: dict[str, Any]) -> str:
        """Get priority display value."""
        return get_priority(fields)

    @staticmethod
    def _get_user_display(user: dict[str, Any] | None) -> str:
        """Get user display name."""
        return get_user_display(user)

    @staticmethod
    def _format_date(date_str: str | None) -> str:
        """Format ISO date string for display."""
        return format_date(date_str)


__all__ = [
    # Backward compatibility
    "JiraFormatter",
    "JiraDocumentBuilder",
    "DocumentBuilder",
    "EpicBuilder",
    "IssueBuilder",
    "SubtaskBuilder",
    # Display functions
    "format_issue",
    "format_issues_table",
    "format_projects_table",
    "format_transitions_table",
    # Formatters
    "format_date",
    "format_date_relative",
    "get_priority",
    "get_user_display",
    # Builders
    "IssuePanelBuilder",
    "IssueTableBuilder",
    "ProjectTableBuilder",
    "TransitionTableBuilder",
    # ADF
    "extract_text_from_adf",
]
