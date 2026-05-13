"""Tests for updated create command with TypedBuilder."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from temet_jira.cli import jira


@patch("temet_jira.cli.JiraClient")
def test_create_risk_type(mock_client_cls):
    """create --type Risk uses TypedBuilder."""
    mock_client = MagicMock()
    mock_client.create_issue.return_value = {"key": "PROJ-999"}
    mock_client.get_issue.return_value = {
        "key": "PROJ-999",
        "fields": {"summary": "Test Risk", "issuetype": {"name": "Risk"},
                    "status": {"name": "New"}, "priority": {"name": "Medium"}},
    }
    mock_client_cls.return_value = mock_client

    runner = CliRunner()
    result = runner.invoke(jira, [
        "create", "-s", "Test Risk", "--type", "Risk", "--project", "PROJ",
    ])
    assert result.exit_code == 0
    assert "PROJ-999" in result.output

    # Verify issuetype was set correctly
    call_args = mock_client.create_issue.call_args
    fields = call_args[0][0]
    assert fields["issuetype"]["name"] == "Risk"


@patch("temet_jira.cli.JiraClient")
def test_create_help_text_updated(mock_client_cls):
    """create --help shows updated type description."""
    runner = CliRunner()
    result = runner.invoke(jira, ["create", "--help"])
    assert "metadata" in result.output
