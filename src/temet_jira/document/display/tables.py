"""Rich Table builders for displaying Jira data."""

from typing import Any, Self

from rich.table import Table

from temet_jira.document.display.formatters import (
    format_date_relative,
    get_priority,
    get_user_display,
    truncate_summary,
)


def _get_console() -> Any:
    from temet_jira.ui import console
    return console


_ALL_COLUMN_DEFS: list[tuple[str, str, str, bool]] = [
    # (header, data_key, style, no_wrap)
    ("Key",      "key",      "key",    True),
    ("Type",     "type",     "",       False),
    ("Summary",  "summary",  "",       False),
    ("Status",   "status",   "",       False),
    ("Priority", "priority", "accent", False),
    ("Assignee", "assignee", "muted",  False),
    ("Updated",  "updated",  "muted",  False),
]

_DEFAULT_COLUMN_KEYS = ["key", "type", "summary", "status", "assignee", "updated"]


class IssueTableBuilder:
    """Builder for creating Rich Tables displaying Jira issues."""

    def __init__(self, title: str = "Jira Issues") -> None:
        self._title = title
        self._issues: list[dict[str, Any]] = []
        self._max_results: int = 50
        self._col_filter: list[str] | None = None
        self._no_truncate: bool = False
        self._show_headers: bool = True

    def with_issues(self, issues: list[dict[str, Any]]) -> Self:
        self._issues = issues
        return self

    def with_max_results(self, max_results: int) -> Self:
        self._max_results = max_results
        return self

    def with_title(self, title: str) -> Self:
        self._title = title
        return self

    def with_column_filter(self, columns: list[str]) -> Self:
        """Show only the specified columns (lowercase names: key, type, summary, etc.)."""
        self._col_filter = [c.lower() for c in columns]
        return self

    def with_no_truncate(self, no_truncate: bool) -> Self:
        self._no_truncate = no_truncate
        return self

    def with_show_headers(self, show_headers: bool) -> Self:
        self._show_headers = show_headers
        return self

    def _active_columns(self) -> list[tuple[str, str, str, bool]]:
        """Return column defs filtered by col_filter (or default set)."""
        wanted = self._col_filter if self._col_filter is not None else _DEFAULT_COLUMN_KEYS
        return [c for c in _ALL_COLUMN_DEFS if c[1] in wanted]

    def _extract_row_dict(self, issue: dict[str, Any]) -> dict[str, str]:
        from temet_jira.ui.status import format_status
        fields = issue.get("fields", {})
        status_obj = fields.get("status") or {}
        status_name = status_obj.get("name", "Unknown")
        category_key = (status_obj.get("statusCategory") or {}).get("key")
        summary = fields.get("summary", "No Summary")
        if not self._no_truncate:
            summary = truncate_summary(summary, 60)
        return {
            "key": issue.get("key", "N/A"),
            "type": (fields.get("issuetype") or {}).get("name", "Unknown"),
            "summary": summary,
            "status": format_status(status_name, category_key),
            "priority": get_priority(fields),
            "assignee": get_user_display(fields.get("assignee")),
            "updated": format_date_relative(fields.get("updated")),
        }

    def _create_table(self) -> Table:
        displayed = min(len(self._issues), self._max_results)
        title = f"{self._title} (showing {displayed} of {len(self._issues)})"
        table = Table(
            title=title,
            show_header=self._show_headers,
            header_style="header",
            box=None,
            show_edge=False,
            pad_edge=True,
        )
        for header, _key, style, no_wrap in self._active_columns():
            table.add_column(header, style=style or None, no_wrap=no_wrap)
        return table

    def build(self) -> Table:
        table = self._create_table()
        active = self._active_columns()
        for issue in self._issues[: self._max_results]:
            row_dict = self._extract_row_dict(issue)
            table.add_row(*[row_dict[col[1]] for col in active])
        return table

    @classmethod
    def default(
        cls, issues: list[dict[str, Any]], title: str = "Jira Issues", max_results: int = 50
    ) -> Table:
        return cls(title=title).with_issues(issues).with_max_results(max_results).build()


class CompactIssueTableBuilder(IssueTableBuilder):
    """Builder for compact issue tables (fewer columns)."""

    def __init__(self, title: str = "Jira Issues") -> None:
        super().__init__(title)
        self._col_filter = ["key", "summary", "status", "assignee"]


class ProjectTableBuilder:
    """Builder for creating Rich Tables displaying Jira projects."""

    def __init__(self, title: str = "Jira Projects") -> None:
        """Initialize with table title."""
        self._title = title
        self._projects: list[dict[str, Any]] = []

    def with_projects(self, projects: list[dict[str, Any]]) -> Self:
        """Set projects to display."""
        self._projects = projects
        return self

    def build(self) -> Table:
        """Build the Rich Table."""
        table = Table(title=self._title)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Lead", style="green")

        for project in self._projects:
            table.add_row(
                project.get("key", ""),
                project.get("name", ""),
                project.get("projectTypeKey", "Unknown"),
                get_user_display(project.get("lead")),
            )

        return table

    @classmethod
    def default(cls, projects: list[dict[str, Any]]) -> Table:
        """Build table with default configuration."""
        return cls().with_projects(projects).build()


class TransitionTableBuilder:
    """Builder for creating Rich Tables displaying Jira transitions."""

    def __init__(self, title: str = "Available Transitions") -> None:
        """Initialize with table title."""
        self._title = title
        self._transitions: list[dict[str, Any]] = []

    def with_transitions(self, transitions: list[dict[str, Any]]) -> Self:
        """Set transitions to display."""
        self._transitions = transitions
        return self

    def build(self) -> Table:
        """Build the Rich Table."""
        table = Table(title=self._title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("To Status", style="yellow")

        for transition in self._transitions:
            table.add_row(
                transition.get("id", ""),
                transition.get("name", ""),
                transition.get("to", {}).get("name", "Unknown"),
            )

        return table

    @classmethod
    def default(cls, transitions: list[dict[str, Any]]) -> Table:
        """Build table with default configuration."""
        return cls().with_transitions(transitions).build()


def format_issues_table(
    issues: list[dict[str, Any]],
    max_results: int = 50,
    columns: list[str] | None = None,
    no_truncate: bool = False,
    show_headers: bool = True,
) -> None:
    """Format and display multiple Jira issues in a table."""
    c = _get_console()
    if not issues:
        c.print("[warning]No issues found[/warning]")
        return

    builder = (
        IssueTableBuilder()
        .with_issues(issues)
        .with_max_results(max_results)
        .with_no_truncate(no_truncate)
        .with_show_headers(show_headers)
    )
    if columns:
        builder = builder.with_column_filter(columns)
    table = builder.build()
    c.print(table)

    if len(issues) > max_results:
        c.print(
            f"\n[warning]Showing first {max_results} results. "
            "Use --max-results to see more.[/warning]"
        )


def format_projects_table(projects: list[dict[str, Any]]) -> None:
    """Format and display projects in a table."""
    _get_console().print(ProjectTableBuilder.default(projects))


def format_transitions_table(transitions: list[dict[str, Any]]) -> None:
    """Format and display transitions in a table."""
    _get_console().print(TransitionTableBuilder.default(transitions))
