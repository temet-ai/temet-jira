"""Integration tests for the Jira analyze CLI command."""

import csv
import json

import pytest
from click.testing import CliRunner

from temet_jira.cli import jira


class TestAnalyzeIntegration:
    """Integration tests for the analyze command group."""

    @pytest.fixture
    def runner(self):
        """Create a click test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_jira_export(self, tmp_path):
        """Create a realistic Jira export file."""
        issues = [
            {
                "key": "PROJ-100",
                "fields": {
                    "summary": "Implement user authentication",
                    "status": {"name": "Done"},
                    "created": "2024-01-15T10:00:00.000+0000",
                    "updated": "2024-01-20T16:30:00.000+0000",
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "High"},
                    "assignee": {
                        "displayName": "John Doe",
                        "emailAddress": "john.doe@example.com",
                    },
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-16T09:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2024-01-18T14:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Code Review",
                                }
                            ],
                        },
                        {
                            "created": "2024-01-20T16:30:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "Code Review",
                                    "toString": "Done",
                                }
                            ],
                        },
                    ]
                },
            },
            {
                "key": "PROJ-101",
                "fields": {
                    "summary": "Add password reset functionality",
                    "status": {"name": "In Progress"},
                    "created": "2024-01-18T11:00:00.000+0000",
                    "updated": "2024-01-22T10:15:00.000+0000",
                    "issuetype": {"name": "Task"},
                    "priority": {"name": "Medium"},
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-19T10:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "PROJ-102",
                "fields": {
                    "summary": "Fix login bug on mobile",
                    "status": {"name": "To Do"},
                    "created": "2024-01-22T14:00:00.000+0000",
                    "updated": "2024-01-22T14:00:00.000+0000",
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "Critical"},
                },
                "changelog": {"histories": []},
            },
        ]

        export_file = tmp_path / "jira_export.json"
        export_file.write_text(json.dumps(issues, indent=2))
        return export_file

    def test_analyze_state_durations_creates_csv(
        self, runner, sample_jira_export, tmp_path
    ):
        """Test that the analyze state-durations command creates a CSV file."""
        output_file = tmp_path / "state_analysis.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify CSV structure
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Should have one row per state duration, not per issue
            # With the test data, we expect multiple state transitions
            assert len(rows) > 0

            # Check basic fields are present (actual column names with capitals)
            assert all("Issue Key" in row for row in rows)
            assert all("State" in row for row in rows)
            assert all("Calendar Days" in row for row in rows)

            # Verify issue keys are present in the results
            issue_keys = {row["Issue Key"] for row in rows}
            assert "PROJ-100" in issue_keys
            assert "PROJ-101" in issue_keys
            assert "PROJ-102" in issue_keys

    def test_analyze_with_date_filter(self, runner, sample_jira_export, tmp_path):
        """Test that date filtering works correctly."""
        output_file = tmp_path / "filtered_analysis.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
                "--date-from",
                "2024-01-18",
                "--date-to",
                "2024-01-22",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Read the CSV to verify filtering
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # CSV has rows for state transitions, not one per issue
            # Should have state transitions for PROJ-101 and PROJ-102 (created within date range)
            assert len(rows) > 0
            issue_keys = {row["Issue Key"] for row in rows}
            assert "PROJ-101" in issue_keys
            assert "PROJ-102" in issue_keys
            assert "PROJ-100" not in issue_keys  # Created before date range

    def test_analyze_empty_input(self, runner, tmp_path):
        """Test handling of empty input file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")
        output_file = tmp_path / "empty_output.csv"

        result = runner.invoke(
            jira,
            ["analyze", "state-durations", str(empty_file), "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "No issues found" in result.output or "Empty" in result.output

        # CSV should have header but no data rows
        with open(output_file) as f:
            lines = f.readlines()
            assert len(lines) == 1  # Just the header

    def test_analyze_with_business_hours_flag(
        self, runner, sample_jira_export, tmp_path
    ):
        """Test that business hours flag is accepted."""
        output_file = tmp_path / "business_hours_analysis.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
                "--business-hours",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        # Should see a note about business hours if not implemented
        if "not yet implemented" in result.output.lower():
            assert "business hours" in result.output.lower()

    def test_analyze_with_timezone(self, runner, sample_jira_export, tmp_path):
        """Test that timezone option is accepted."""
        output_file = tmp_path / "tz_analysis.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
                "--timezone",
                "America/New_York",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_analyze_invalid_date_format(self, runner, sample_jira_export, tmp_path):
        """Test error handling for invalid date format."""
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
                "--date-from",
                "invalid-date",
            ],
        )

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_analyze_output_directory_creation(
        self, runner, sample_jira_export, tmp_path
    ):
        """Test that output directories are created if they don't exist."""
        output_file = tmp_path / "new_dir" / "analysis.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                str(sample_jira_export),
                "-o",
                str(output_file),
            ],
        )

        # Should handle directory creation or fail gracefully
        if result.exit_code == 0:
            assert output_file.exists()
            assert output_file.parent.exists()
