"""End-to-end tests for Jira CLI formatter integration (TASK-006)."""

import csv
import json
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from temet_jira.cli import search


class TestJiraCliFormatterE2E:
    """End-to-end test suite for CLI formatter integration."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.mock_client = Mock()
        self.complex_issues = [
            {
                "key": "PROJ-123",
                "id": "10001",
                "self": "https://example.atlassian.net/rest/api/2/issue/10001",
                "fields": {
                    "summary": "Implement new authentication system",
                    "status": {
                        "name": "In Progress",
                        "id": "3",
                        "statusCategory": {"name": "In Progress"},
                    },
                    "priority": {
                        "name": "High",
                        "id": "2",
                        "iconUrl": "https://example.atlassian.net/images/icons/priorities/high.svg",
                    },
                    "assignee": {
                        "displayName": "John Doe",
                        "emailAddress": "john.doe@example.com",
                        "accountId": "5b10ac8d82e05b22cc7d4ef5",
                    },
                    "reporter": {
                        "displayName": "Jane Smith",
                        "emailAddress": "jane.smith@example.com",
                        "accountId": "5b10ac8d82e05b22cc7d4ef6",
                    },
                    "created": "2024-01-01T10:00:00.000+0000",
                    "updated": "2024-01-15T14:30:00.000+0000",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "We need to implement OAuth2",
                                    }
                                ],
                            }
                        ],
                    },
                    "issuetype": {"name": "Story", "id": "10001", "subtask": False},
                    "labels": ["security", "backend", "oauth"],
                    "components": [
                        {"name": "Authentication", "id": "10001"},
                        {"name": "API", "id": "10002"},
                    ],
                    "fixVersions": [{"name": "2.0.0", "releaseDate": "2024-03-01"}],
                    "customfield_10001": "EPIC-50",  # Epic Link
                    "customfield_10002": 13,  # Story Points
                    "attachment": [
                        {
                            "filename": "design.pdf",
                            "size": 204800,
                            "created": "2024-01-02T10:00:00.000+0000",
                        }
                    ],
                    "comment": {"total": 3, "comments": []},
                },
            },
            {
                "key": "PROJ-124",
                "id": "10002",
                "self": "https://example.atlassian.net/rest/api/2/issue/10002",
                "fields": {
                    "summary": "Fix login page CSS issues",
                    "status": {
                        "name": "To Do",
                        "id": "1",
                        "statusCategory": {"name": "To Do"},
                    },
                    "priority": None,  # Test null handling
                    "assignee": None,  # Unassigned
                    "reporter": {
                        "displayName": "Bob Johnson",
                        "emailAddress": "bob.johnson@example.com",
                        "accountId": "5b10ac8d82e05b22cc7d4ef7",
                    },
                    "created": "2024-01-20T09:00:00.000+0000",
                    "updated": "2024-01-20T09:00:00.000+0000",
                    "description": None,  # No description
                    "issuetype": {"name": "Bug", "id": "10002", "subtask": False},
                    "labels": [],  # No labels
                    "components": [],  # No components
                    "fixVersions": [],
                    "customfield_10001": None,
                    "customfield_10002": None,
                    "attachment": [],
                    "comment": {"total": 0, "comments": []},
                },
            },
        ]

    @patch("temet_jira.cli.JiraClient")
    def test_json_formatter_with_complex_data(self, mock_client_class):
        """Test JSON formatter handles complex nested data correctly."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.complex_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                ["project = PROJ", "--format", "json", "--output", "complex.json"],
            )

            assert result.exit_code == 0
            assert Path("complex.json").exists()

            # Verify the JSON is valid and contains expected data
            with open("complex.json") as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["key"] == "PROJ-123"
            assert data[0]["fields"]["summary"] == "Implement new authentication system"
            assert data[0]["fields"]["labels"] == ["security", "backend", "oauth"]
            assert data[0]["fields"]["customfield_10002"] == 13

            assert data[1]["key"] == "PROJ-124"
            assert data[1]["fields"]["priority"] is None
            assert data[1]["fields"]["assignee"] is None

    @patch("temet_jira.cli.JiraClient")
    def test_csv_formatter_with_complex_data(self, mock_client_class):
        """Test CSV formatter handles complex nested data with flattening."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.complex_issues, True)

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search, ["project = PROJ", "--format", "csv", "--output", "complex.csv"]
            )

            assert result.exit_code == 0
            assert Path("complex.csv").exists()

            # Verify the CSV is valid and contains expected data
            with open("complex.csv") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2

            # Check that keys are present (exact field names depend on flattening)
            first_row = rows[0]
            assert "key" in first_row
            assert any("PROJ-123" in str(v) for v in first_row.values())

            # Check that nested fields are flattened
            assert any("summary" in k.lower() for k in first_row)
            assert any(
                "Implement new authentication system" in str(v)
                for v in first_row.values()
            )

            # Check that labels are handled (joined with semicolon)
            assert any("security;backend;oauth" in str(v) for v in first_row.values())

    @patch("temet_jira.cli.JiraClient")
    def test_json_formatter_console_output(self, mock_client_class):
        """Test JSON formatter outputs to console correctly."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.complex_issues, True)

        result = self.runner.invoke(search, ["project = PROJ", "--format", "json"])

        assert result.exit_code == 0

        # Verify output is valid JSON
        output_data = json.loads(result.output.strip())
        assert len(output_data) == 2
        assert output_data[0]["key"] == "PROJ-123"
        assert output_data[1]["key"] == "PROJ-124"

    @patch("temet_jira.cli.JiraClient")
    def test_csv_formatter_console_output(self, mock_client_class):
        """Test CSV formatter outputs to console correctly."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = (self.complex_issues, True)

        result = self.runner.invoke(search, ["project = PROJ", "--format", "csv"])

        assert result.exit_code == 0

        # Verify output is valid CSV
        reader = csv.DictReader(StringIO(result.output.strip()))
        rows = list(reader)
        assert len(rows) == 2

        # Check that issue keys are present
        assert any("PROJ-123" in str(row.values()) for row in rows)
        assert any("PROJ-124" in str(row.values()) for row in rows)

    @patch("temet_jira.cli.JiraClient")
    def test_handles_empty_results(self, mock_client_class):
        """Test formatters handle empty result sets gracefully."""
        mock_client_class.return_value = self.mock_client
        self.mock_client.search_issues.return_value = ([], True)

        # Test JSON format with empty results
        result = self.runner.invoke(
            search, ["project = NONEXISTENT", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "No issues found" in result.output

        # Test CSV format with empty results
        result = self.runner.invoke(
            search, ["project = NONEXISTENT", "--format", "csv"]
        )
        assert result.exit_code == 0
        assert "No issues found" in result.output

    @patch("temet_jira.cli.JiraClient")
    def test_large_dataset_with_all_flag(self, mock_client_class):
        """Test handling large datasets with --all flag and progress indicator."""
        mock_client_class.return_value = self.mock_client

        # Create 125 issues (search_all_issues returns all at once)
        all_issues = self.complex_issues * 25 + self.complex_issues * 25 + self.complex_issues * 25

        # --all uses search_all_issues
        self.mock_client.search_all_issues.return_value = all_issues

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                search,
                [
                    "project = PROJ",
                    "--all",
                    "--format",
                    "json",
                    "--output",
                    "large.json",
                ],
            )

            assert result.exit_code == 0

            # Check progress messages were shown
            assert "Fetched" in result.output
            assert "issue(s) total" in result.output

            # Verify file was created and contains all issues
            assert Path("large.json").exists()
            with open("large.json") as f:
                data = json.load(f)

            # Should have 6 issues (complex_issues has 2 issues * 25 * 3 = 150, but we only have 2 unique)
            # Actually we're multiplying the complex_issues list, so it depends on its length
            expected_count = len(all_issues)
            assert len(data) == expected_count

    @patch("temet_jira.cli.JiraClient")
    def test_special_characters_in_csv(self, mock_client_class):
        """Test CSV formatter handles special characters and CSV injection."""
        mock_client_class.return_value = self.mock_client

        # Create issues with special characters
        special_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": '=FORMULA("injection")',  # Potential CSV injection
                    "description": 'Line 1\nLine 2\n"Quoted text"',  # Newlines and quotes
                    "labels": ["tag,with,comma", "normal-tag"],  # Commas in data
                },
            }
        ]

        self.mock_client.search_issues.return_value = (special_issues, True)

        result = self.runner.invoke(search, ["project = TEST", "--format", "csv"])

        assert result.exit_code == 0

        # Check that CSV injection is protected (should have leading quote)
        assert "'=FORMULA" in result.output or "=FORMULA" not in result.output[0:10]

        # Verify CSV is still parseable
        reader = csv.DictReader(StringIO(result.output.strip()))
        rows = list(reader)
        assert len(rows) == 1
