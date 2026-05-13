"""Tests for display table builders."""

from unittest.mock import patch

import pytest
from rich.table import Table

from temet_jira.document.display.tables import (
    CompactIssueTableBuilder,
    IssueTableBuilder,
    ProjectTableBuilder,
    TransitionTableBuilder,
    format_issues_table,
    format_projects_table,
    format_transitions_table,
)


@pytest.fixture
def sample_issues() -> list[dict]:
    """Sample list of Jira issues for testing."""
    return [
        {
            "key": "TEST-1",
            "fields": {
                "summary": "First issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Task"},
                "assignee": {"displayName": "John Doe"},
                "updated": "2024-01-15T10:00:00Z",
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "summary": "Second issue with a very long summary that should be truncated",
                "status": {"name": "In Progress"},
                "priority": None,
                "issuetype": {"name": "Bug"},
                "assignee": None,
                "updated": "2024-01-16T14:30:00Z",
            },
        },
    ]


@pytest.fixture
def sample_projects() -> list[dict]:
    """Sample list of Jira projects for testing."""
    return [
        {
            "key": "PROJ",
            "name": "Project Name",
            "projectTypeKey": "software",
            "lead": {"displayName": "Project Lead"},
        },
        {
            "key": "TEST",
            "name": "Test Project",
            "projectTypeKey": "business",
            "lead": None,
        },
    ]


@pytest.fixture
def sample_transitions() -> list[dict]:
    """Sample list of Jira transitions for testing."""
    return [
        {"id": "1", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "2", "name": "Done", "to": {"name": "Closed"}},
    ]


class TestIssueTableBuilder:
    """Tests for IssueTableBuilder class."""

    def test_build_returns_table(self, sample_issues: list[dict]) -> None:
        """build returns a Rich Table."""
        builder = IssueTableBuilder()
        table = builder.with_issues(sample_issues).build()
        assert isinstance(table, Table)

    def test_with_title(self, sample_issues: list[dict]) -> None:
        """with_title sets custom title."""
        builder = IssueTableBuilder()
        table = builder.with_title("Custom Title").with_issues(sample_issues).build()
        assert isinstance(table, Table)

    def test_with_max_results(self, sample_issues: list[dict]) -> None:
        """with_max_results limits displayed issues."""
        builder = IssueTableBuilder()
        table = builder.with_issues(sample_issues).with_max_results(1).build()
        assert isinstance(table, Table)
        # Table should have only 1 row
        assert table.row_count == 1

    def test_default_classmethod(self, sample_issues: list[dict]) -> None:
        """default classmethod builds table with defaults."""
        table = IssueTableBuilder.default(sample_issues)
        assert isinstance(table, Table)
        assert table.row_count == 2

    def test_method_chaining(self, sample_issues: list[dict]) -> None:
        """Methods can be chained."""
        table = (
            IssueTableBuilder()
            .with_title("Chained")
            .with_issues(sample_issues)
            .with_max_results(50)
            .build()
        )
        assert isinstance(table, Table)

    def test_empty_issues(self) -> None:
        """Empty issues list creates table with no rows."""
        table = IssueTableBuilder.default([])
        assert table.row_count == 0


class TestCompactIssueTableBuilder:
    """Tests for CompactIssueTableBuilder class."""

    def test_build_returns_table(self, sample_issues: list[dict]) -> None:
        """build returns a Rich Table."""
        builder = CompactIssueTableBuilder()
        table = builder.with_issues(sample_issues).build()
        assert isinstance(table, Table)

    def test_fewer_columns_than_full(self, sample_issues: list[dict]) -> None:
        """Compact table has fewer columns than full table."""
        compact = CompactIssueTableBuilder().with_issues(sample_issues).build()
        full = IssueTableBuilder().with_issues(sample_issues).build()
        # Rich Table uses .columns list, not column_count property
        assert len(compact.columns) < len(full.columns)


class TestProjectTableBuilder:
    """Tests for ProjectTableBuilder class."""

    def test_build_returns_table(self, sample_projects: list[dict]) -> None:
        """build returns a Rich Table."""
        builder = ProjectTableBuilder()
        table = builder.with_projects(sample_projects).build()
        assert isinstance(table, Table)
        assert table.row_count == 2

    def test_default_classmethod(self, sample_projects: list[dict]) -> None:
        """default classmethod builds table with defaults."""
        table = ProjectTableBuilder.default(sample_projects)
        assert isinstance(table, Table)

    def test_empty_projects(self) -> None:
        """Empty projects list creates table with no rows."""
        table = ProjectTableBuilder.default([])
        assert table.row_count == 0

    def test_missing_lead(self, sample_projects: list[dict]) -> None:
        """Missing lead is handled gracefully."""
        table = ProjectTableBuilder.default(sample_projects)
        assert table.row_count == 2


class TestTransitionTableBuilder:
    """Tests for TransitionTableBuilder class."""

    def test_build_returns_table(self, sample_transitions: list[dict]) -> None:
        """build returns a Rich Table."""
        builder = TransitionTableBuilder()
        table = builder.with_transitions(sample_transitions).build()
        assert isinstance(table, Table)
        assert table.row_count == 2

    def test_default_classmethod(self, sample_transitions: list[dict]) -> None:
        """default classmethod builds table with defaults."""
        table = TransitionTableBuilder.default(sample_transitions)
        assert isinstance(table, Table)

    def test_empty_transitions(self) -> None:
        """Empty transitions list creates table with no rows."""
        table = TransitionTableBuilder.default([])
        assert table.row_count == 0


class TestFormatIssuesTable:
    """Tests for format_issues_table function."""

    @patch("temet_jira.ui.console")
    def test_empty_list_shows_message(self, mock_console) -> None:
        """Empty issues list shows 'No issues found' message."""
        format_issues_table([])
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "No issues found" in call_args

    @patch("temet_jira.ui.console")
    def test_prints_table(self, mock_console, sample_issues: list[dict]) -> None:
        """Valid issues list prints table to console."""
        format_issues_table(sample_issues)
        mock_console.print.assert_called()

    @patch("temet_jira.ui.console")
    def test_max_results_exceeded_shows_message(self, mock_console) -> None:
        """When max_results exceeded, shows message."""
        issues = [
            {"key": f"TEST-{i}", "fields": {"summary": f"Issue {i}", "status": {"name": "Open"}}}
            for i in range(100)
        ]
        format_issues_table(issues, max_results=50)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Showing first 50 results" in c for c in calls)

    @patch("temet_jira.ui.console")
    def test_custom_max_results(self, mock_console, sample_issues: list[dict]) -> None:
        """Custom max_results is respected."""
        format_issues_table(sample_issues, max_results=1)
        mock_console.print.assert_called()


class TestFormatProjectsTable:
    """Tests for format_projects_table function."""

    @patch("temet_jira.ui.console")
    def test_prints_table(self, mock_console, sample_projects: list[dict]) -> None:
        """Valid projects list prints table to console."""
        format_projects_table(sample_projects)
        mock_console.print.assert_called()


class TestFormatTransitionsTable:
    """Tests for format_transitions_table function."""

    @patch("temet_jira.ui.console")
    def test_prints_table(self, mock_console, sample_transitions: list[dict]) -> None:
        """Valid transitions list prints table to console."""
        format_transitions_table(sample_transitions)
        mock_console.print.assert_called()
