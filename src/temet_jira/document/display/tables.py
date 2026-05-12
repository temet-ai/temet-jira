"""Rich Table builders for displaying Jira data."""

from typing import Any, Self

from rich.console import Console
from rich.table import Table

from temet_jira.document.display.formatters import (
    format_date,
    format_date_relative,
    get_priority,
    get_user_display,
    truncate_summary,
)

console = Console()


class IssueTableBuilder:
    """Builder for creating Rich Tables displaying Jira issues."""

    def __init__(self, title: str = "Jira Issues") -> None:
        """Initialize with table title."""
        self._title = title
        self._issues: list[dict[str, Any]] = []
        self._max_results: int = 50
        self._columns: list[tuple[str, str, bool]] = []  # (name, style, no_wrap)
        self._setup_default_columns()

    def _setup_default_columns(self) -> None:
        """Set up default column configuration."""
        self._columns = [
            ("Key", "cyan", True),
            ("Type", "green", False),
            ("Summary", "white", False),
            ("Status", "yellow", False),
            ("Priority", "magenta", False),
            ("Assignee", "green", False),
            ("Updated", "blue", False),
        ]

    def with_issues(self, issues: list[dict[str, Any]]) -> Self:
        """Set issues to display."""
        self._issues = issues
        return self

    def with_max_results(self, max_results: int) -> Self:
        """Set maximum results to display."""
        self._max_results = max_results
        return self

    def with_title(self, title: str) -> Self:
        """Set table title."""
        self._title = title
        return self

    def _create_table(self) -> Table:
        """Create the Rich Table with configured columns."""
        displayed = min(len(self._issues), self._max_results)
        title = f"{self._title} (showing {displayed} of {len(self._issues)})"
        table = Table(title=title)

        for name, style, no_wrap in self._columns:
            table.add_column(name, style=style, no_wrap=no_wrap)

        return table

    def _extract_row(self, issue: dict[str, Any]) -> tuple[str, ...]:
        """Extract row data from an issue."""
        fields = issue.get("fields", {})

        key = issue.get("key", "N/A")
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")
        summary = truncate_summary(fields.get("summary", "No Summary"), 60)
        status = fields.get("status", {}).get("name", "Unknown")
        priority = get_priority(fields)
        assignee = get_user_display(fields.get("assignee"))
        updated = format_date_relative(fields.get("updated"))

        return (key, issue_type, summary, status, priority, assignee, updated)

    def build(self) -> Table:
        """Build the Rich Table."""
        table = self._create_table()

        for issue in self._issues[: self._max_results]:
            table.add_row(*self._extract_row(issue))

        return table

    @classmethod
    def default(
        cls, issues: list[dict[str, Any]], title: str = "Jira Issues", max_results: int = 50
    ) -> Table:
        """Build table with default configuration."""
        return (
            cls(title=title)
            .with_issues(issues)
            .with_max_results(max_results)
            .build()
        )


class CompactIssueTableBuilder(IssueTableBuilder):
    """Builder for compact issue tables (fewer columns)."""

    def _setup_default_columns(self) -> None:
        """Set up compact column configuration."""
        self._columns = [
            ("Key", "cyan", True),
            ("Summary", "white", False),
            ("Status", "yellow", False),
            ("Priority", "magenta", False),
            ("Assignee", "green", False),
            ("Updated", "blue", False),
        ]

    def _extract_row(self, issue: dict[str, Any]) -> tuple[str, ...]:
        """Extract row data for compact view."""
        fields = issue.get("fields", {})

        key = issue.get("key", "N/A")
        summary = truncate_summary(fields.get("summary", "No Summary"), 50)
        status = fields.get("status", {}).get("name", "Unknown")
        priority = get_priority(fields)
        assignee = get_user_display(fields.get("assignee"))
        updated = format_date(fields.get("updated"))

        return (key, summary, status, priority, assignee, updated)


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


def format_issues_table(issues: list[dict[str, Any]], max_results: int = 50) -> None:
    """Format and display multiple Jira issues in a table."""
    if not issues:
        console.print("[yellow]No issues found[/yellow]")
        return

    table = IssueTableBuilder.default(issues, max_results=max_results)
    console.print(table)

    if len(issues) > max_results:
        console.print(
            f"\n[yellow]Showing first {max_results} results. "
            "Use --max-results to see more.[/yellow]"
        )


def format_projects_table(projects: list[dict[str, Any]]) -> None:
    """Format and display projects in a table."""
    console.print(ProjectTableBuilder.default(projects))


def format_transitions_table(transitions: list[dict[str, Any]]) -> None:
    """Format and display transitions in a table."""
    console.print(TransitionTableBuilder.default(transitions))
