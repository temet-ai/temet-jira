"""Tests for jira-tool types command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from jira_tool.cli import jira


@patch("jira_tool.cli.JiraClient")
def test_types_command_displays_table(mock_client_cls):
    """types command shows issue types in a table."""
    mock_client = MagicMock()
    mock_client.get_issue_types.return_value = [
        {"name": "Task", "subtask": False},
        {"name": "Risk", "subtask": False},
        {"name": "Sub-task", "subtask": True},
    ]
    mock_client_cls.return_value = mock_client

    runner = CliRunner()
    result = runner.invoke(jira, ["types", "--project", "WPCW"])
    assert result.exit_code == 0
    assert "Task" in result.output
    assert "Risk" in result.output
    assert "Sub-task" in result.output


@patch("jira_tool.cli.JiraClient")
def test_types_command_default_project(mock_client_cls):
    """types command uses JIRA_DEFAULT_PROJECT."""
    mock_client = MagicMock()
    mock_client.get_issue_types.return_value = [{"name": "Bug", "subtask": False}]
    mock_client_cls.return_value = mock_client

    runner = CliRunner(env={"JIRA_DEFAULT_PROJECT": "MYPROJ"})
    result = runner.invoke(jira, ["types"])
    assert result.exit_code == 0
    mock_client.get_issue_types.assert_called_once_with("MYPROJ")
