"""Terminal display formatting for Jira data using Rich library."""

from jira_tool.document.display.formatters import (
    format_date,
    format_date_relative,
    get_priority,
    get_user_display,
    truncate_summary,
)
from jira_tool.document.display.panels import (
    IssueHeaderBuilder,
    IssuePanelBuilder,
    format_issue,
)
from jira_tool.document.display.tables import (
    IssueTableBuilder,
    ProjectTableBuilder,
    TransitionTableBuilder,
    format_issues_table,
    format_projects_table,
    format_transitions_table,
)

__all__ = [
    # Formatters
    "format_date",
    "format_date_relative",
    "get_priority",
    "get_user_display",
    "truncate_summary",
    # Panels
    "IssueHeaderBuilder",
    "IssuePanelBuilder",
    "format_issue",
    # Tables
    "IssueTableBuilder",
    "ProjectTableBuilder",
    "TransitionTableBuilder",
    "format_issues_table",
    "format_projects_table",
    "format_transitions_table",
]
