"""Tests for the get CLI command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from temet_jira.cli import jira

MOCK_ISSUE = {
    "key": "TEST-1",
    "fields": {"summary": "Test", "status": {"name": "Open"}},
}


class TestGetCommand:
    """Tests for the get CLI command."""

    @pytest.fixture
    def runner(self):
        """Create a click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_client(self):
        """Create a mocked JiraClient."""
        with patch("temet_jira.cli.JiraClient") as mock_cls:
            client_instance = MagicMock()
            client_instance.get_issue.return_value = MOCK_ISSUE
            client_instance.get_comments.return_value = [
                {"id": "1", "body": "A comment"},
            ]
            mock_cls.return_value = client_instance
            yield client_instance

    def test_get_help(self, runner):
        """Test that get --help shows expected options."""
        result = runner.invoke(jira, ["get", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output" in result.output
        assert "--expand" in result.output
        assert "--comments" in result.output

    def test_get_default_table_format(self, runner, mock_client):
        """Test get command with explicit table format calls format_issue."""
        with patch("temet_jira.cli.format_issue") as mock_format:
            result = runner.invoke(jira, ["get", "TEST-1", "--format", "table"])

            assert result.exit_code == 0
            mock_client.get_issue.assert_called_once_with("TEST-1", expand=["names"])
            mock_format.assert_called_once_with(MOCK_ISSUE, comments=None, show_all_fields=False)

    def test_get_json_format(self, runner, mock_client):
        """Test get command with JSON format."""
        result = runner.invoke(jira, ["get", "TEST-1", "-f", "json"])

        assert result.exit_code == 0
        # Verify output is valid JSON
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert output_data[0]["key"] == "TEST-1"

    def test_get_jsonl_format(self, runner, mock_client):
        """Test get command with JSONL format."""
        result = runner.invoke(jira, ["get", "TEST-1", "-f", "jsonl"])

        assert result.exit_code == 0
        # JSONL: each line is a valid JSON object
        lines = [line for line in result.output.strip().split("\n") if line]
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["key"] == "TEST-1"

    def test_get_with_expand(self, runner, mock_client):
        """Test get command with --expand option."""
        with patch("temet_jira.cli.format_issue"):
            result = runner.invoke(
                jira, ["get", "TEST-1", "--expand", "changelog,transitions"]
            )

            assert result.exit_code == 0
            mock_client.get_issue.assert_called_once_with(
                "TEST-1", expand=["changelog", "transitions", "names"]
            )

    def test_get_with_comments_flag(self, runner, mock_client):
        """Test get command with --comments flag fetches comments."""
        with patch("temet_jira.cli.format_issue") as mock_format:
            result = runner.invoke(jira, ["get", "TEST-1", "--comments", "--format", "table"])

            assert result.exit_code == 0
            mock_client.get_comments.assert_called_once_with("TEST-1")
            # format_issue should be called with the comments list
            mock_format.assert_called_once_with(
                MOCK_ISSUE,
                comments=[{"id": "1", "body": "A comment"}],
                show_all_fields=False,
            )

    def test_get_json_output_to_file(self, runner, mock_client, tmp_path):
        """Test get command writing JSON output to a file."""
        output_file = tmp_path / "issue.json"

        result = runner.invoke(
            jira, ["get", "TEST-1", "-f", "json", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify file content is valid JSON with the issue data
        file_content = json.loads(output_file.read_text())
        assert isinstance(file_content, list)
        assert file_content[0]["key"] == "TEST-1"
