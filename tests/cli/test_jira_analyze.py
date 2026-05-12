"""Tests for Jira analyze command."""

import csv
import json

import pytest
from click.testing import CliRunner

from temet_jira.cli import jira as cli


class TestJiraAnalyzeCommand:
    """Tests for the jira analyze command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_issues(self):
        """Create sample issues with changelog data."""
        return [
            {
                "key": "TEST-1",
                "fields": {
                    "created": "2024-01-01T09:00:00.000+0000",
                    "status": {"name": "Done"},
                    "summary": "Test issue 1",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-02T10:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2024-01-05T14:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        },
                    ]
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "created": "2024-01-03T09:00:00.000+0000",
                    "status": {"name": "In Progress"},
                    "summary": "Test issue 2",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-04T11:00:00.000+0000",
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
        ]

    def test_analyze_command_exists(self, runner):
        """Test that analyze command exists in jira group."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output

        # Check for state-durations subcommand
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "state-durations" in result.output

    def test_analyze_basic_workflow(self, runner, sample_issues, tmp_path):
        """Test basic analyze workflow: JSON input -> CSV output."""
        # Create input JSON file
        input_file = tmp_path / "issues.json"
        input_file.write_text(json.dumps(sample_issues))

        # Create output CSV file path
        output_file = tmp_path / "durations.csv"

        # Run the analyze command
        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
            ],
        )

        if result.exit_code != 0:
            print(f"Command output:\n{result.output}")
            print(f"Exception:\n{result.exception}")
        assert result.exit_code == 0
        assert output_file.exists()

        # Verify CSV contents
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Should have rows for each state of each issue
            assert len(rows) > 0

            # Check required columns - now using the proper format_as_csv output
            first_row = rows[0]
            print(f"Actual columns: {list(first_row.keys())}")
            assert "Issue Key" in first_row
            assert "State" in first_row
            assert "Start Time" in first_row
            assert "End Time" in first_row
            assert "Calendar Days" in first_row

    def test_analyze_with_date_filter(self, runner, sample_issues, tmp_path):
        """Test analyze command with date filtering."""
        input_file = tmp_path / "issues.json"
        input_file.write_text(json.dumps(sample_issues))
        output_file = tmp_path / "durations.csv"

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
                "--date-from",
                "2024-01-02",
                "--date-to",
                "2024-01-04",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_analyze_with_business_hours(self, runner, sample_issues, tmp_path):
        """Test analyze command with business hours calculation."""
        input_file = tmp_path / "issues.json"
        input_file.write_text(json.dumps(sample_issues))
        output_file = tmp_path / "durations.csv"

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
                "--business-hours",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify CSV was created (business hours might not be in column headers with current implementation)
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            # The business hours flag affects calculation but may not add a separate column
            # in the current implementation

    def test_analyze_file_not_found(self, runner):
        """Test analyze command with non-existent file."""
        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                "/non/existent/file.json",
                "--output",
                "output.csv",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_analyze_invalid_json(self, runner, tmp_path):
        """Test analyze command with invalid JSON file."""
        input_file = tmp_path / "invalid.json"
        input_file.write_text("{ invalid json }")

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                "output.csv",
            ],
        )

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "error" in result.output.lower()

    def test_analyze_empty_issues(self, runner, tmp_path):
        """Test analyze command with empty issues list."""
        input_file = tmp_path / "empty.json"
        input_file.write_text("[]")
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "No issues" in result.output or "empty" in result.output.lower()

    def test_analyze_output_permission_error(self, runner, sample_issues, tmp_path):
        """Test analyze command with write permission error."""
        input_file = tmp_path / "issues.json"
        input_file.write_text(json.dumps(sample_issues))

        # Use a path that likely doesn't have write permission
        output_file = "/root/protected.csv"

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                output_file,
            ],
        )

        # Should handle the error gracefully
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "permission" in result.output.lower()

    def test_analyze_large_file_performance(self, runner, tmp_path):
        """Test analyze command with large number of issues."""
        # Generate 1000 issues
        large_issues = []
        for i in range(1000):
            large_issues.append(
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "created": "2024-01-01T09:00:00.000+0000",
                        "status": {"name": "Done"},
                        "summary": f"Test issue {i}",
                    },
                    "changelog": {
                        "histories": [
                            {
                                "created": "2024-01-02T10:00:00.000+0000",
                                "items": [
                                    {
                                        "field": "status",
                                        "fromString": "To Do",
                                        "toString": "Done",
                                    }
                                ],
                            }
                        ]
                    },
                }
            )

        input_file = tmp_path / "large.json"
        input_file.write_text(json.dumps(large_issues))
        output_file = tmp_path / "large_output.csv"

        import time

        start_time = time.time()

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
            ],
        )

        elapsed_time = time.time() - start_time

        assert result.exit_code == 0
        assert output_file.exists()
        # Should process 1000 issues in reasonable time (< 10 seconds)
        assert elapsed_time < 10

    def test_analyze_with_current_states(self, runner, tmp_path):
        """Test handling of issues still in progress (no end time)."""
        issues_with_current = [
            {
                "key": "CURRENT-1",
                "fields": {
                    "created": "2024-01-01T09:00:00.000+0000",
                    "status": {"name": "In Progress"},
                    "summary": "Currently in progress",
                },
                "changelog": {"histories": []},
            }
        ]

        input_file = tmp_path / "current.json"
        input_file.write_text(json.dumps(issues_with_current))
        output_file = tmp_path / "current_output.csv"

        result = runner.invoke(
            cli,
            [
                "analyze",
                "state-durations",
                str(input_file),
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            # The new implementation has proper columns
            assert "Issue Key" in rows[0]
            assert rows[0]["Issue Key"] == "CURRENT-1"
            assert rows[0]["State"] == "In Progress"
            assert rows[0]["End Time"] == "Current"  # Current state has no end time
