"""Tests for Jira CLI search command option parsing."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from temet_jira.cli import search


class TestJiraSearchOptions:
    """Test suite for Jira search CLI options."""

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
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "summary": "Test Issue 2",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Medium"},
                    "assignee": None,
                    "updated": "2024-01-02T12:00:00Z",
                    "description": "Test description 2",
                    "issuetype": {"name": "Bug"},
                },
            },
        ]

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_fields_option(self, mock_client_class):
        """Test search command with --fields option."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(
            search, ["project = TEST", "--fields", "summary,status,priority"]
        )

        assert result.exit_code == 0
        self.mock_client.search_issues.assert_called_once_with(
            "project = TEST",
            max_results=None,
            fields=["summary", "status", "priority"],
            expand=None,
        )

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_expand_option(self, mock_client_class):
        """Test search command with --expand option."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(
            search, ["project = TEST", "--expand", "changelog,transitions"]
        )

        assert result.exit_code == 0
        self.mock_client.search_issues.assert_called_once_with(
            "project = TEST",
            max_results=None,
            fields=None,
            expand=["changelog", "transitions"],
        )

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_output_file_json(self, mock_client_class):
        """Test search command with --output and --format json."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                ["project = TEST", "--output", "results.json", "--format", "json"],
            )

            assert result.exit_code == 0

            # Check that output file was created with JSON content
            assert Path("results.json").exists()
            with open("results.json") as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["key"] == "TEST-1"
                assert data[1]["key"] == "TEST-2"

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_output_file_csv(self, mock_client_class):
        """Test search command with --output and --format csv."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search, ["project = TEST", "--output", "results.csv", "--format", "csv"]
            )

            assert result.exit_code == 0

            # Check that output file was created with CSV content
            assert Path("results.csv").exists()
            with open("results.csv") as f:
                content = f.read()
                # The new CSV formatter uses flattened structure, so check for key fields
                assert "TEST-1" in content
                assert "TEST-2" in content
                # Check that it contains some expected field names (flattened format)
                assert "key" in content.lower() or "fields.summary" in content.lower()

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_format_table_default(
        self, mock_client_class
    ):
        """Test search command with --format table (default)."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "table"])

        assert result.exit_code == 0

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_all_option(self, mock_client_class):
        """Test search command with --all option to fetch all results."""
        mock_client_class.return_value = self.mock_client

        # --all flag uses search_all_issues, which returns all results
        all_issues = [self.mock_issues[0]] * 50 + [self.mock_issues[1]] * 30
        self.mock_client.search_all_issues.return_value = all_issues

        result = self.runner.invoke(search, ["project = TEST", "--all"])

        assert result.exit_code == 0
        # Should have called search_all_issues once
        self.mock_client.search_all_issues.assert_called_once()

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_invalid_format(self, mock_client_class):
        """Test search command with invalid --format option."""
        mock_client_class.return_value = self.mock_client

        result = self.runner.invoke(search, ["project = TEST", "--format", "invalid"])

        # Should fail with validation error
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_multiple_options(self, mock_client_class):
        """Test search command with multiple options combined."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                [
                    "project = TEST",
                    "--fields",
                    "summary,status",
                    "--expand",
                    "changelog",
                    "--max-results",
                    "5",
                    "--output",
                    "results.json",
                    "--format",
                    "json",
                ],
            )

            assert result.exit_code == 0
            self.mock_client.search_issues.assert_called_once_with(
                "project = TEST",
                max_results=5,
                fields=["summary", "status"],
                expand=["changelog"],
            )

            # Check output file
            assert Path("results.json").exists()

    @patch("temet_jira.cli.JiraClient")
    def test_search_format_json_to_console(self, mock_client_class):
        """Test search command with --format json without output file."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "json"])

        assert result.exit_code == 0
        # Output should contain JSON formatted data
        assert "TEST-1" in result.output
        assert "TEST-2" in result.output
        # Should be valid JSON
        json_output = json.loads(result.output.strip())
        assert len(json_output) == 2

    @patch("temet_jira.cli.JiraClient")
    def test_search_format_csv_to_console(self, mock_client_class):
        """Test search command with --format csv without output file."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "csv"])

        assert result.exit_code == 0
        # Output should contain CSV formatted data
        # The new CSV formatter uses flattened structure
        assert "TEST-1" in result.output
        assert "TEST-2" in result.output
        # Should have CSV header row with field names
        lines = result.output.strip().split("\n")
        assert len(lines) >= 3  # Header + 2 data rows

    @patch("temet_jira.cli.JiraClient")
    def test_search_empty_fields_and_expand(self, mock_client_class):
        """Test search command with empty --fields and --expand options."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.mock_issues, True)

        result = self.runner.invoke(
            search, ["project = TEST", "--fields", "", "--expand", ""]
        )

        assert result.exit_code == 0
        self.mock_client.search_issues.assert_called_once_with(
            "project = TEST",
            max_results=None,
            fields=None,  # Empty string should be treated as None
            expand=None,  # Empty string should be treated as None
        )

    @patch("temet_jira.cli.JiraClient")
    def test_search_with_all_and_max_results(self, mock_client_class):
        """Test that --all option overrides --max-results."""
        mock_client_class.return_value = self.mock_client
        # --all uses search_all_issues which handles pagination internally
        all_issues = self.mock_issues * 25
        self.mock_client.search_all_issues.return_value = all_issues

        result = self.runner.invoke(
            search, ["project = TEST", "--all", "--max-results", "5"]
        )

        assert result.exit_code == 0
        # --all should use search_all_issues, ignoring max-results
        self.mock_client.search_all_issues.assert_called_once()
        # Verify max_per_page is None (will use default 300 in search_all_issues)
        call_args = self.mock_client.search_all_issues.call_args
        assert call_args[1].get("max_per_page") is None
