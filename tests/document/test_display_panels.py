"""Tests for display panel builders."""

from typing import Any
from unittest.mock import patch

import pytest
from rich.panel import Panel

from temet_jira.document.display.panels import (
    IssueHeaderBuilder,
    IssuePanelBuilder,
    format_issue,
)


@pytest.fixture
def sample_issue() -> dict:
    """Sample Jira issue for testing."""
    return {
        "key": "TEST-123",
        "fields": {
            "summary": "Test issue summary",
            "status": {"name": "Open"},
            "priority": {"name": "High"},
            "issuetype": {"name": "Task"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "Jane Smith"},
            "created": "2024-01-15T10:00:00Z",
            "updated": "2024-01-16T14:30:00Z",
            "components": [{"name": "API"}, {"name": "Backend"}],
            "labels": ["urgent", "bug"],
        },
    }


@pytest.fixture
def minimal_issue() -> dict:
    """Minimal issue with only required fields."""
    return {
        "key": "MIN-1",
        "fields": {
            "summary": "Minimal issue",
            "status": {"name": "Open"},
        },
    }


class TestIssuePanelBuilder:
    """Tests for IssuePanelBuilder class."""

    def test_add_key(self, sample_issue: dict) -> None:
        """add_key adds issue key to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_key().build_lines()
        assert any("TEST-123" in line for line in lines)

    def test_add_summary(self, sample_issue: dict) -> None:
        """add_summary adds summary to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_summary().build_lines()
        assert any("Test issue summary" in line for line in lines)

    def test_add_status(self, sample_issue: dict) -> None:
        """add_status adds status to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_status().build_lines()
        assert any("Open" in line for line in lines)

    def test_add_priority(self, sample_issue: dict) -> None:
        """add_priority adds priority to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_priority().build_lines()
        assert any("High" in line for line in lines)

    def test_add_type(self, sample_issue: dict) -> None:
        """add_type adds issue type to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_type().build_lines()
        assert any("Task" in line for line in lines)

    def test_add_assignee(self, sample_issue: dict) -> None:
        """add_assignee adds assignee to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_assignee().build_lines()
        assert any("John Doe" in line for line in lines)

    def test_add_reporter(self, sample_issue: dict) -> None:
        """add_reporter adds reporter to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_reporter().build_lines()
        assert any("Jane Smith" in line for line in lines)

    def test_add_created(self, sample_issue: dict) -> None:
        """add_created adds created date to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_created().build_lines()
        assert any("2024-01-15" in line for line in lines)

    def test_add_updated(self, sample_issue: dict) -> None:
        """add_updated adds updated date to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_updated().build_lines()
        assert any("2024-01-16" in line for line in lines)

    def test_add_components(self, sample_issue: dict) -> None:
        """add_components adds components to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_components().build_lines()
        assert any("API" in line and "Backend" in line for line in lines)

    def test_add_components_empty(self, minimal_issue: dict) -> None:
        """add_components with no components adds nothing."""
        builder = IssuePanelBuilder(minimal_issue)
        lines = builder.add_components().build_lines()
        assert len(lines) == 0

    def test_add_labels(self, sample_issue: dict) -> None:
        """add_labels adds labels to lines."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_labels().build_lines()
        assert any("urgent" in line and "bug" in line for line in lines)

    def test_add_labels_empty(self, minimal_issue: dict) -> None:
        """add_labels with no labels adds nothing."""
        builder = IssuePanelBuilder(minimal_issue)
        lines = builder.add_labels().build_lines()
        assert len(lines) == 0

    def test_add_all_standard(self, sample_issue: dict) -> None:
        """add_all_standard adds all standard fields."""
        builder = IssuePanelBuilder(sample_issue)
        lines = builder.add_all_standard().build_lines()
        # Should have key, summary, status, priority, type, assignee, reporter, dates, components, labels
        assert len(lines) >= 10

    def test_build_returns_panel(self, sample_issue: dict) -> None:
        """build returns a Rich Panel."""
        builder = IssuePanelBuilder(sample_issue)
        panel = builder.add_key().build()
        assert isinstance(panel, Panel)

    def test_default_classmethod(self, sample_issue: dict) -> None:
        """default classmethod builds complete panel."""
        panel = IssuePanelBuilder.default(sample_issue)
        assert isinstance(panel, Panel)

    def test_method_chaining(self, sample_issue: dict) -> None:
        """Methods can be chained."""
        lines = (
            IssuePanelBuilder(sample_issue)
            .add_key()
            .add_summary()
            .add_status()
            .build_lines()
        )
        assert len(lines) == 3


class TestIssueHeaderBuilder:
    """Tests for IssueHeaderBuilder class."""

    def test_build_returns_table(self, sample_issue: dict) -> None:
        """build returns a Rich Table."""
        from rich.table import Table

        builder = IssueHeaderBuilder(sample_issue)
        table = builder.add_key().build()
        assert isinstance(table, Table)

    def test_build_panel_returns_panel(self, sample_issue: dict) -> None:
        """build_panel returns a Rich Panel."""
        builder = IssueHeaderBuilder(sample_issue)
        panel = builder.add_key().build_panel()
        assert isinstance(panel, Panel)

    def test_default_classmethod(self, sample_issue: dict) -> None:
        """default classmethod builds complete panel."""
        panel = IssueHeaderBuilder.default(sample_issue)
        assert isinstance(panel, Panel)


class TestFormatIssue:
    """Tests for format_issue function."""

    @patch("temet_jira.document.display.panels.console")
    def test_invalid_issue_shows_error(self, mock_console) -> None:
        """Invalid issue data shows error message."""
        format_issue({})
        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Invalid" in call_args or "red" in call_args

    @patch("temet_jira.document.display.panels.console")
    def test_valid_issue_prints_panel(self, mock_console, sample_issue: dict) -> None:
        """Valid issue prints panel to console."""
        format_issue(sample_issue)
        mock_console.print.assert_called()

    @patch("temet_jira.document.display.panels.console")
    def test_issue_with_description(self, mock_console) -> None:
        """Issue with description prints description."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "description": "Plain text description",
            },
        }
        format_issue(issue)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Description" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_issue_with_adf_description(self, mock_console) -> None:
        """Issue with ADF description extracts text."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "ADF content"}],
                        }
                    ],
                },
            },
        }
        format_issue(issue)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("ADF content" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_issue_with_labels(self, mock_console) -> None:
        """Issue with labels prints labels."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "labels": ["urgent", "important"],
            },
        }
        format_issue(issue)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("urgent" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_issue_with_parent(self, mock_console) -> None:
        """Issue with parent prints parent key."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "parent": {"key": "EPIC-100"},
            },
        }
        format_issue(issue)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("EPIC-100" in c for c in calls)


@pytest.fixture
def enhanced_issue() -> dict:
    """Enhanced Jira issue with all new fields for testing."""
    return {
        "key": "TEST-456",
        "fields": {
            "summary": "Enhanced issue",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "High"},
            "resolution": {"name": "Done"},
            "components": [{"name": "API"}],
            "fixVersions": [{"name": "1.0.0"}],
            "labels": ["backend"],
            "customfield_10016": 5,
            "customfield_10020": [{"name": "Sprint 10", "state": "active"}],
            "parent": {"key": "EPIC-10", "fields": {"summary": "Parent Epic"}},
            "subtasks": [
                {
                    "key": "TEST-457",
                    "fields": {
                        "summary": "Subtask 1",
                        "status": {"name": "Open"},
                    },
                },
            ],
            "issuelinks": [
                {
                    "type": {"outward": "blocks"},
                    "outwardIssue": {
                        "key": "TEST-458",
                        "fields": {
                            "summary": "Blocked issue",
                            "status": {"name": "Open"},
                        },
                    },
                }
            ],
            "attachment": [
                {"filename": "screenshot.png", "size": 102400},
            ],
        },
    }


class TestIssueHeaderBuilderNewMethods:
    """Tests for newly added IssueHeaderBuilder methods."""

    def test_add_resolution_present(self, enhanced_issue: dict) -> None:
        """add_resolution adds resolution name when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_resolution().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Done" in output

    def test_add_resolution_absent(self, minimal_issue: dict) -> None:
        """add_resolution skips row when resolution is absent."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_resolution().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Resolution" not in output

    def test_add_resolution_none(self) -> None:
        """add_resolution skips row when resolution is None."""
        from io import StringIO

        from rich.console import Console as _Console

        issue = {
            "key": "TEST-1",
            "fields": {"summary": "Test", "status": {"name": "Open"}, "resolution": None},
        }
        builder = IssueHeaderBuilder(issue)
        table = builder.add_resolution().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Resolution" not in output

    def test_add_components(self, enhanced_issue: dict) -> None:
        """add_components adds component names when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_components().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "API" in output

    def test_add_components_absent(self, minimal_issue: dict) -> None:
        """add_components skips row when components list is empty."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_components().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Components" not in output

    def test_add_fix_versions(self, enhanced_issue: dict) -> None:
        """add_fix_versions adds version names when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_fix_versions().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "1.0.0" in output

    def test_add_fix_versions_absent(self, minimal_issue: dict) -> None:
        """add_fix_versions skips row when fixVersions is empty."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_fix_versions().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Fix Versions" not in output

    def test_add_labels(self, enhanced_issue: dict) -> None:
        """add_labels adds labels when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_labels().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "backend" in output

    def test_add_labels_absent(self, minimal_issue: dict) -> None:
        """add_labels skips row when labels list is empty."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_labels().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Labels" not in output

    def test_add_story_points(self, enhanced_issue: dict) -> None:
        """add_story_points adds customfield_10016 when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_story_points().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "5" in output

    def test_add_story_points_none(self, minimal_issue: dict) -> None:
        """add_story_points skips row when customfield_10016 is None."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_story_points().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Story Points" not in output

    def test_add_sprint(self, enhanced_issue: dict) -> None:
        """add_sprint shows sprint name and state from customfield_10020."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_sprint().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Sprint 10" in output
        assert "active" in output

    def test_add_sprint_absent(self, minimal_issue: dict) -> None:
        """add_sprint skips row when customfield_10020 is absent."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_sprint().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Sprint" not in output

    def test_add_parent(self, enhanced_issue: dict) -> None:
        """add_parent shows parent key and summary when present."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_parent().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "EPIC-10" in output
        assert "Parent Epic" in output

    def test_add_parent_absent(self, minimal_issue: dict) -> None:
        """add_parent skips row when parent is absent."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(minimal_issue)
        table = builder.add_parent().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Parent" not in output

    def test_add_all_standard_includes_new_fields(self, enhanced_issue: dict) -> None:
        """add_all_standard includes resolution, components, fix_versions, labels, story_points, sprint, parent."""
        from io import StringIO

        from rich.console import Console as _Console

        builder = IssueHeaderBuilder(enhanced_issue)
        table = builder.add_all_standard().build()

        buf = StringIO()
        _Console(file=buf, width=120).print(table)
        output = buf.getvalue()
        assert "Done" in output  # resolution
        assert "API" in output  # components
        assert "1.0.0" in output  # fix versions
        assert "backend" in output  # labels
        assert "5" in output  # story points
        assert "Sprint 10" in output  # sprint
        assert "EPIC-10" in output  # parent


def _render_all_console_output(mock_console: Any) -> str:
    """Render all objects printed to mock console into a single string.

    Rich Table objects need to be rendered through a real Console to extract
    their text content; simple str() on mock call args does not include row data.
    """
    from io import StringIO

    from rich.console import Console as _Console

    parts: list[str] = []
    for call in mock_console.print.call_args_list:
        for arg in call.args:
            buf = StringIO()
            _Console(file=buf, width=200).print(arg)
            parts.append(buf.getvalue())
    return "\n".join(parts)


class TestFormatIssueSubtasks:
    """Tests for subtasks display in format_issue."""

    @patch("temet_jira.document.display.panels.console")
    def test_subtasks_displayed(self, mock_console, enhanced_issue: dict) -> None:
        """Subtasks render a table with key, summary, and status."""
        format_issue(enhanced_issue)
        output = _render_all_console_output(mock_console)
        assert "Subtasks" in output
        assert "TEST-457" in output
        assert "Subtask 1" in output

    @patch("temet_jira.document.display.panels.console")
    def test_no_subtasks_no_section(self, mock_console, minimal_issue: dict) -> None:
        """No subtasks section when subtasks list is empty."""
        format_issue(minimal_issue)
        output = _render_all_console_output(mock_console)
        assert "Subtasks" not in output


class TestFormatIssueLinkedIssues:
    """Tests for linked issues display in format_issue."""

    @patch("temet_jira.document.display.panels.console")
    def test_outward_links_displayed(self, mock_console, enhanced_issue: dict) -> None:
        """Outward linked issues render relation, key, summary, status."""
        format_issue(enhanced_issue)
        output = _render_all_console_output(mock_console)
        assert "Linked Issues" in output
        assert "TEST-458" in output
        assert "blocks" in output

    @patch("temet_jira.document.display.panels.console")
    def test_inward_links_displayed(self, mock_console) -> None:
        """Inward linked issues render with inward relation label."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "issuelinks": [
                    {
                        "type": {"inward": "is blocked by"},
                        "inwardIssue": {
                            "key": "TEST-999",
                            "fields": {
                                "summary": "Blocker",
                                "status": {"name": "Done"},
                            },
                        },
                    }
                ],
            },
        }
        format_issue(issue)
        output = _render_all_console_output(mock_console)
        assert "Linked Issues" in output
        assert "TEST-999" in output
        assert "is blocked by" in output

    @patch("temet_jira.document.display.panels.console")
    def test_no_links_no_section(self, mock_console, minimal_issue: dict) -> None:
        """No linked issues section when issuelinks list is absent."""
        format_issue(minimal_issue)
        output = _render_all_console_output(mock_console)
        assert "Linked Issues" not in output


class TestFormatIssueAttachments:
    """Tests for attachments display in format_issue."""

    @patch("temet_jira.document.display.panels.console")
    def test_attachments_displayed(self, mock_console, enhanced_issue: dict) -> None:
        """Attachments render a table with filename and human-readable size."""
        format_issue(enhanced_issue)
        output = _render_all_console_output(mock_console)
        assert "Attachments" in output
        assert "screenshot.png" in output
        # 102400 bytes = 100.0 KB
        assert "100.0 KB" in output

    @patch("temet_jira.document.display.panels.console")
    def test_no_attachments_no_section(self, mock_console, minimal_issue: dict) -> None:
        """No attachments section when attachment list is absent."""
        format_issue(minimal_issue)
        output = _render_all_console_output(mock_console)
        assert "Attachments" not in output


class TestFormatIssueComments:
    """Tests for comments display in format_issue."""

    @patch("temet_jira.document.display.panels.console")
    def test_comments_displayed(self, mock_console) -> None:
        """Passing comments list to format_issue renders author, date, and body."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
            },
        }
        comments = [
            {
                "author": {"displayName": "Alice"},
                "created": "2024-03-10T08:00:00Z",
                "body": "This is a comment",
            },
        ]
        format_issue(issue, comments=comments)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Comments" in c for c in calls)
        assert any("Alice" in c for c in calls)
        assert any("This is a comment" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_multiple_comments(self, mock_console) -> None:
        """Multiple comments are all displayed."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
            },
        }
        comments = [
            {
                "author": {"displayName": "Alice"},
                "created": "2024-03-10T08:00:00Z",
                "body": "First comment",
            },
            {
                "author": {"displayName": "Bob"},
                "created": "2024-03-11T09:00:00Z",
                "body": "Second comment",
            },
        ]
        format_issue(issue, comments=comments)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Alice" in c for c in calls)
        assert any("Bob" in c for c in calls)
        assert any("First comment" in c for c in calls)
        assert any("Second comment" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_no_comments_no_section(self, mock_console) -> None:
        """No comments section when comments is None."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
            },
        }
        format_issue(issue, comments=None)
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert not any("Comments" in c for c in calls)

    @patch("temet_jira.document.display.panels.console")
    def test_empty_comments_no_section(self, mock_console) -> None:
        """No comments section when comments list is empty."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
            },
        }
        format_issue(issue, comments=[])
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert not any("Comments" in c for c in calls)


class TestFormatIssueBackwardCompatibility:
    """Tests that format_issue backward compatibility is preserved."""

    @patch("temet_jira.document.display.panels.console")
    def test_call_without_comments_arg(self, mock_console) -> None:
        """Calling format_issue(issue) without comments arg does not raise."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
            },
        }
        # Should not raise -- comments defaults to None
        format_issue(issue)
        mock_console.print.assert_called()

    @patch("temet_jira.document.display.panels.console")
    def test_positional_only_arg(self, mock_console, sample_issue: dict) -> None:
        """Calling format_issue with only positional issue works as before."""
        format_issue(sample_issue)
        mock_console.print.assert_called()
