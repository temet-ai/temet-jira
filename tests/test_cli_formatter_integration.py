"""Tests for Jira CLI formatter integration (TASK-006)."""

import csv
import json
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from temet_jira.cli import search


class TestJiraCliFormatterIntegration:
    """Test suite for CLI formatter integration."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.mock_client = Mock()
        self.mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue 1",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "John Doe"},
                    "updated": "2024-01-01T12:00:00Z",
                    "description": "Test description 1",
                    "issuetype": {"name": "Task"},
                    "created": "2024-01-01T10:00:00Z",
                    "reporter": {"displayName": "Jane Smith"},
                    "labels": ["backend", "urgent"],
                    "components": [{"name": "API"}],
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "summary": "Test Issue 2",
                    "status": {"name": "In Progress"},
                    "priority": None,  # Test null handling
                    "assignee": None,
                    "updated": "2024-01-02T12:00:00Z",
                    "description": "Test description 2",
                    "issuetype": {"name": "Bug"},
                    "created": "2024-01-02T10:00:00Z",
                    "reporter": {"displayName": "Bob Johnson"},
                    "labels": [],
                    "components": [],
                },
            },
        ]

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_json")
    def test_uses_json_formatter_when_format_json(
        self, mock_format_json, mock_client_class
    ):
        """Test that CLI uses format_as_json when --format json is specified."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_json.return_value = '{"test": "json"}'

        result = self.runner.invoke(search, ["project = TEST", "--format", "json"])

        assert result.exit_code == 0
        # Should have called the JSON formatter
        mock_format_json.assert_called_once_with(self.mock_issues)
        # Output should contain the formatted JSON
        assert '{"test": "json"}' in result.output

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_csv")
    def test_uses_csv_formatter_when_format_csv(
        self, mock_format_csv, mock_client_class
    ):
        """Test that CLI uses format_as_csv when --format csv is specified."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_csv.return_value = "Key,Summary\nTEST-1,Test Issue 1\n"

        result = self.runner.invoke(search, ["project = TEST", "--format", "csv"])

        assert result.exit_code == 0
        # Should have called the CSV formatter
        mock_format_csv.assert_called_once_with(self.mock_issues)
        # Output should contain the formatted CSV
        assert "Key,Summary" in result.output
        assert "TEST-1,Test Issue 1" in result.output

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_json")
    def test_writes_json_to_file_when_output_specified(
        self, mock_format_json, mock_client_class
    ):
        """Test that JSON output is written to file when --output is specified."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_json.return_value = '{"test": "json"}'

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                ["project = TEST", "--format", "json", "--output", "results.json"],
            )

            assert result.exit_code == 0
            # Should have called the JSON formatter
            mock_format_json.assert_called_once_with(self.mock_issues)

            # File should exist and contain the formatted data
            assert Path("results.json").exists()
            with open("results.json") as f:
                assert f.read() == '{"test": "json"}'

            # Should show success message
            assert "✓" in result.output
            assert "results.json" in result.output

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_csv")
    def test_writes_csv_to_file_when_output_specified(
        self, mock_format_csv, mock_client_class
    ):
        """Test that CSV output is written to file when --output is specified."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_csv.return_value = "Key,Summary\nTEST-1,Test Issue 1\n"

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search, ["project = TEST", "--format", "csv", "--output", "results.csv"]
            )

            assert result.exit_code == 0
            # Should have called the CSV formatter
            mock_format_csv.assert_called_once_with(self.mock_issues)

            # File should exist and contain the formatted data
            assert Path("results.csv").exists()
            with open("results.csv") as f:
                assert f.read() == "Key,Summary\nTEST-1,Test Issue 1\n"

            # Should show success message
            assert "✓" in result.output
            assert "results.csv" in result.output

    @patch("temet_jira.cli.JiraClient")
    def test_table_format_warns_when_output_specified(
        self, mock_client_class
    ):
        """Test that table format shows warning when --output is specified."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                ["project = TEST", "--format", "table", "--output", "results.txt"],
            )

            assert result.exit_code == 0
            # Should show warning about table format not being saveable
            assert "Table format cannot be saved to file" in result.output
            # File should NOT be created
            assert not Path("results.txt").exists()

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.err_console")
    def test_shows_progress_for_large_fetches_with_all(
        self, mock_err_console, mock_client_class
    ):
        """Test that progress indicator is shown when fetching all results."""
        mock_client_class.return_value = self.mock_client

        # --all uses search_all_issues which returns all results at once
        all_issues = self.mock_issues * 25 + self.mock_issues * 15

        self.mock_client.search_all_issues.return_value = all_issues

        result = self.runner.invoke(
            search, ["project = TEST", "--all", "--format", "json"]
        )

        assert result.exit_code == 0
        # Should show progress messages via err_console
        assert mock_err_console.status.called
        # Check that status was used with appropriate messages
        status_calls = mock_err_console.status.call_args_list
        assert any("Fetching all issues" in str(call) for call in status_calls)

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_json")
    def test_handles_file_write_error_gracefully(
        self, mock_format_json, mock_client_class
    ):
        """Test that file write errors are handled gracefully."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_json.return_value = '{"test": "json"}'

        with self.runner.isolated_filesystem():
            # Create a directory with the same name as the output file
            Path("results.json").mkdir()

            result = self.runner.invoke(
                search,
                ["project = TEST", "--format", "json", "--output", "results.json"],
            )

            # Should handle the error gracefully
            assert result.exit_code != 0

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_json")
    def test_formatter_error_handling(self, mock_format_json, mock_client_class):
        """Test that formatter errors are handled gracefully."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_json.side_effect = Exception("Formatting error")

        result = self.runner.invoke(search, ["project = TEST", "--format", "json"])

        # Should handle the error gracefully
        assert result.exit_code != 0

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_json")
    @patch("temet_jira.cli.click.echo")
    def test_json_output_to_stdout_uses_click_echo(
        self, mock_echo, mock_format_json, mock_client_class
    ):
        """Test that JSON output to stdout uses click.echo."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_json.return_value = '{"test": "json"}'

        result = self.runner.invoke(search, ["project = TEST", "--format", "json"])

        assert result.exit_code == 0
        # Should have called click.echo with the formatted JSON
        mock_echo.assert_called_with('{"test": "json"}')

    @patch("temet_jira.cli.JiraClient")
    @patch("temet_jira.cli.format_as_csv")
    @patch("temet_jira.cli.click.echo")
    def test_csv_output_to_stdout_uses_click_echo(
        self, mock_echo, mock_format_csv, mock_client_class
    ):
        """Test that CSV output to stdout uses click.echo."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)
        mock_format_csv.return_value = "Key,Summary\nTEST-1,Test Issue 1\n"

        result = self.runner.invoke(search, ["project = TEST", "--format", "csv"])

        assert result.exit_code == 0
        # Should have called click.echo with the formatted CSV
        mock_echo.assert_called_with("Key,Summary\nTEST-1,Test Issue 1\n")

    @patch("temet_jira.cli.JiraClient")
    def test_real_json_formatting_integration(self, mock_client_class):
        """Test real JSON formatting without mocking the formatter."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "json"])

        assert result.exit_code == 0
        # Output should be valid JSON
        output_data = json.loads(result.output.strip())
        assert len(output_data) == 2
        assert output_data[0]["key"] == "TEST-1"
        assert output_data[1]["key"] == "TEST-2"

    @patch("temet_jira.cli.JiraClient")
    def test_real_csv_formatting_integration(self, mock_client_class):
        """Test real CSV formatting without mocking the formatter."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "csv"])

        assert result.exit_code == 0
        # Output should be valid CSV
        csv_reader = csv.DictReader(StringIO(result.output.strip()))
        rows = list(csv_reader)
        assert len(rows) == 2
        # Check that key field exists in flattened CSV
        assert any("TEST-1" in str(row.values()) for row in rows)
        assert any("TEST-2" in str(row.values()) for row in rows)

    @patch("temet_jira.cli.JiraClient")
    def test_progress_messages_with_all_option(self, mock_client_class):
        """Test that progress messages are shown during pagination."""
        mock_client_class.return_value = self.mock_client

        # --all uses search_all_issues which returns all results at once
        all_issues = self.mock_issues * 25 + self.mock_issues * 25 + self.mock_issues * 10
        self.mock_client.search_all_issues.return_value = all_issues

        result = self.runner.invoke(
            search, ["project = TEST", "--all", "--format", "json"]
        )

        assert result.exit_code == 0
        # Check that completion message was shown
        assert "Fetched" in result.output and "issue(s) total" in result.output
