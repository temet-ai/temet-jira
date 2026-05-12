"""Behavioral tests for the temet-jira MCP server.

Tests verify that each MCP tool function:
- Calls the correct JiraClient method with the right arguments
- Returns the expected shape
- Handles missing/optional parameters correctly
- Propagates errors from the client
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import temet_jira.mcp_server as mcp_server_module
from temet_jira.mcp_server import (
    add_comment,
    create_issue,
    get_epics,
    get_issue,
    get_issue_types,
    get_transitions,
    mcp,
    search_issues,
    transition_issue,
    update_issue,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Reset the lazy client singleton between tests."""
    original = mcp_server_module._client
    mcp_server_module._client = None
    yield
    mcp_server_module._client = original


@pytest.fixture
def mock_client():
    """Patch _get_client to return a fresh MagicMock for every test."""
    client = MagicMock()
    with patch("temet_jira.mcp_server._get_client", return_value=client):
        yield client


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


class TestToolRegistration:
    """Verify all 9 tools are registered with FastMCP."""

    def _registered_tool_names(self) -> set[str]:
        """Return the set of tool names registered with the MCP app."""
        # FastMCP stores components with keys like "tool:<name>@<version>"
        components = mcp._local_provider._components
        return {
            key.split(":")[1].split("@")[0]
            for key in components
            if key.startswith("tool:")
        }

    def test_all_nine_tools_registered(self):
        """FastMCP app must expose exactly the 9 documented tools."""
        tool_names = self._registered_tool_names()
        expected = {
            "get_issue",
            "search_issues",
            "create_issue",
            "update_issue",
            "add_comment",
            "get_transitions",
            "transition_issue",
            "get_epics",
            "get_issue_types",
        }
        assert expected == tool_names

    def test_mcp_app_name(self):
        """Server must be named 'temet-jira'."""
        assert mcp.name == "temet-jira"


# ---------------------------------------------------------------------------
# get_issue
# ---------------------------------------------------------------------------


class TestGetIssue:
    """Tests for the get_issue tool."""

    def test_returns_client_payload(self, mock_client):
        """get_issue returns exactly what the client returns."""
        payload: dict[str, Any] = {
            "key": "PROJ-1",
            "fields": {"summary": "Login broken", "status": {"name": "Open"}},
        }
        mock_client.get_issue.return_value = payload

        result = get_issue("PROJ-1")

        assert result == payload

    def test_passes_key_to_client(self, mock_client):
        """get_issue forwards the key argument."""
        mock_client.get_issue.return_value = {}

        get_issue("PROJ-42")

        mock_client.get_issue.assert_called_once_with("PROJ-42", expand=None)

    def test_passes_expand_list(self, mock_client):
        """get_issue forwards expand as a list."""
        mock_client.get_issue.return_value = {}

        get_issue("PROJ-1", expand=["changelog", "transitions"])

        mock_client.get_issue.assert_called_once_with(
            "PROJ-1", expand=["changelog", "transitions"]
        )

    def test_expand_defaults_to_none(self, mock_client):
        """expand parameter defaults to None when omitted."""
        mock_client.get_issue.return_value = {}

        get_issue("PROJ-1")

        _, kwargs = mock_client.get_issue.call_args
        assert kwargs["expand"] is None

    def test_propagates_client_error(self, mock_client):
        """get_issue lets exceptions from JiraClient bubble up."""
        mock_client.get_issue.side_effect = ValueError("Issue not found: PROJ-999")

        with pytest.raises(ValueError, match="PROJ-999"):
            get_issue("PROJ-999")


# ---------------------------------------------------------------------------
# search_issues
# ---------------------------------------------------------------------------


class TestSearchIssues:
    """Tests for the search_issues tool."""

    def test_returns_issues_and_is_last(self, mock_client):
        """search_issues wraps client result in {issues, is_last} dict."""
        issues_list = [{"key": "PROJ-1"}, {"key": "PROJ-2"}]
        mock_client.search_issues.return_value = (issues_list, True)

        result = search_issues("project = PROJ")

        assert result == {"issues": issues_list, "is_last": True}

    def test_passes_jql_to_client(self, mock_client):
        """search_issues forwards the JQL string."""
        mock_client.search_issues.return_value = ([], True)
        jql = "assignee = currentUser() ORDER BY updated DESC"

        search_issues(jql)

        call_kwargs = mock_client.search_issues.call_args[1]
        assert call_kwargs["jql"] == jql

    def test_default_max_results_is_50(self, mock_client):
        """max_results defaults to 50."""
        mock_client.search_issues.return_value = ([], True)

        search_issues("project = PROJ")

        call_kwargs = mock_client.search_issues.call_args[1]
        assert call_kwargs["max_results"] == 50

    def test_custom_max_results(self, mock_client):
        """max_results is forwarded to client."""
        mock_client.search_issues.return_value = ([], True)

        search_issues("project = PROJ", max_results=10)

        call_kwargs = mock_client.search_issues.call_args[1]
        assert call_kwargs["max_results"] == 10

    def test_optional_fields_forwarded(self, mock_client):
        """fields parameter is forwarded to client."""
        mock_client.search_issues.return_value = ([], True)

        search_issues("project = PROJ", fields=["summary", "status"])

        call_kwargs = mock_client.search_issues.call_args[1]
        assert call_kwargs["fields"] == ["summary", "status"]

    def test_optional_expand_forwarded(self, mock_client):
        """expand parameter is forwarded to client."""
        mock_client.search_issues.return_value = ([], True)

        search_issues("project = PROJ", expand=["changelog"])

        call_kwargs = mock_client.search_issues.call_args[1]
        assert call_kwargs["expand"] == ["changelog"]

    def test_is_last_false_when_more_pages(self, mock_client):
        """is_last=False is correctly reflected in the return value."""
        mock_client.search_issues.return_value = ([{"key": "PROJ-1"}], False)

        result = search_issues("project = PROJ", max_results=1)

        assert result["is_last"] is False

    def test_propagates_client_error(self, mock_client):
        """search_issues lets JiraClient exceptions bubble up."""
        mock_client.search_issues.side_effect = ConnectionError("Jira unreachable")

        with pytest.raises(ConnectionError):
            search_issues("project = PROJ")


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


class TestCreateIssue:
    """Tests for the create_issue tool."""

    def test_passes_required_fields(self, mock_client):
        """project, summary, and issue_type are always passed to client."""
        mock_client.create_issue.return_value = {"key": "PROJ-99", "id": "12345"}

        create_issue(project="PROJ", summary="Fix login", issue_type="Bug")

        call_args = mock_client.create_issue.call_args[0][0]
        assert call_args["project"] == {"key": "PROJ"}
        assert call_args["summary"] == "Fix login"
        assert call_args["issuetype"] == {"name": "Bug"}

    def test_default_issue_type_is_task(self, mock_client):
        """issue_type defaults to 'Task' when omitted."""
        mock_client.create_issue.return_value = {"key": "PROJ-100"}

        create_issue(project="PROJ", summary="Do something")

        fields = mock_client.create_issue.call_args[0][0]
        assert fields["issuetype"] == {"name": "Task"}

    def test_description_wrapped_in_adf(self, mock_client):
        """Plain-text description is wrapped in an ADF paragraph."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(project="PROJ", summary="S", description="Some text")

        fields = mock_client.create_issue.call_args[0][0]
        adf = fields["description"]
        assert adf["type"] == "doc"
        assert adf["version"] == 1
        assert adf["content"][0]["type"] == "paragraph"
        assert adf["content"][0]["content"][0]["text"] == "Some text"

    def test_description_omitted_when_none(self, mock_client):
        """description key is absent from fields when not provided."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(project="PROJ", summary="S")

        fields = mock_client.create_issue.call_args[0][0]
        assert "description" not in fields

    def test_priority_passed_correctly(self, mock_client):
        """priority is wrapped in {"name": ...} dict."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(project="PROJ", summary="S", priority="High")

        fields = mock_client.create_issue.call_args[0][0]
        assert fields["priority"] == {"name": "High"}

    def test_labels_passed_as_list(self, mock_client):
        """labels list is forwarded unchanged."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(project="PROJ", summary="S", labels=["backend", "urgent"])

        fields = mock_client.create_issue.call_args[0][0]
        assert fields["labels"] == ["backend", "urgent"]

    def test_assignee_id_wrapped_correctly(self, mock_client):
        """assignee_id is wrapped in {"accountId": ...} dict."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(project="PROJ", summary="S", assignee_id="abc123")

        fields = mock_client.create_issue.call_args[0][0]
        assert fields["assignee"] == {"accountId": "abc123"}

    def test_extra_fields_merged(self, mock_client):
        """extra_fields are merged into the fields dict."""
        mock_client.create_issue.return_value = {"key": "PROJ-1"}

        create_issue(
            project="PROJ",
            summary="S",
            extra_fields={"customfield_10001": "value"},
        )

        fields = mock_client.create_issue.call_args[0][0]
        assert fields["customfield_10001"] == "value"

    def test_returns_client_response(self, mock_client):
        """create_issue returns whatever the client returns."""
        created = {"key": "PROJ-50", "id": "9999", "self": "https://..."}
        mock_client.create_issue.return_value = created

        result = create_issue(project="PROJ", summary="Test issue")

        assert result == created

    def test_propagates_client_error(self, mock_client):
        """create_issue lets JiraClient exceptions bubble up."""
        mock_client.create_issue.side_effect = RuntimeError("Invalid project key")

        with pytest.raises(RuntimeError, match="Invalid project key"):
            create_issue(project="BADKEY", summary="S")


# ---------------------------------------------------------------------------
# update_issue
# ---------------------------------------------------------------------------


class TestUpdateIssue:
    """Tests for the update_issue tool."""

    def test_calls_client_with_key_and_fields(self, mock_client):
        """update_issue passes key and fields dict to client."""
        update_issue("PROJ-10", {"summary": "New title"})

        mock_client.update_issue.assert_called_once_with(
            "PROJ-10", {"summary": "New title"}
        )

    def test_returns_ok_status_with_key(self, mock_client):
        """update_issue returns {status: ok, key: ...}."""
        result = update_issue("PROJ-10", {"priority": {"name": "Low"}})

        assert result == {"status": "ok", "key": "PROJ-10"}

    def test_propagates_client_error(self, mock_client):
        """update_issue lets JiraClient exceptions bubble up."""
        mock_client.update_issue.side_effect = PermissionError("Not authorized")

        with pytest.raises(PermissionError):
            update_issue("PROJ-10", {"summary": "X"})


# ---------------------------------------------------------------------------
# add_comment
# ---------------------------------------------------------------------------


class TestAddComment:
    """Tests for the add_comment tool."""

    def test_wraps_body_in_adf(self, mock_client):
        """Plain text body is automatically wrapped in an ADF doc."""
        mock_client.add_comment.return_value = {"id": "123"}

        add_comment("PROJ-5", "Fixed in PR #42")

        call_args = mock_client.add_comment.call_args
        key_arg = call_args[0][0]
        adf_arg = call_args[0][1]

        assert key_arg == "PROJ-5"
        assert adf_arg["type"] == "doc"
        assert adf_arg["version"] == 1
        assert adf_arg["content"][0]["type"] == "paragraph"
        assert adf_arg["content"][0]["content"][0]["text"] == "Fixed in PR #42"

    def test_returns_client_response(self, mock_client):
        """add_comment returns whatever the client returns."""
        comment_data: dict[str, Any] = {"id": "999", "body": "..."}
        mock_client.add_comment.return_value = comment_data

        result = add_comment("PROJ-5", "Some comment")

        assert result == comment_data

    def test_propagates_client_error(self, mock_client):
        """add_comment lets JiraClient exceptions bubble up."""
        mock_client.add_comment.side_effect = ValueError("Issue not found")

        with pytest.raises(ValueError, match="Issue not found"):
            add_comment("PROJ-999", "Comment text")


# ---------------------------------------------------------------------------
# get_transitions
# ---------------------------------------------------------------------------


class TestGetTransitions:
    """Tests for the get_transitions tool."""

    def test_passes_key_to_client(self, mock_client):
        """get_transitions forwards the issue key."""
        mock_client.get_transitions.return_value = []

        get_transitions("PROJ-7")

        mock_client.get_transitions.assert_called_once_with("PROJ-7")

    def test_returns_transitions_list(self, mock_client):
        """get_transitions returns the list from the client."""
        transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            {"id": "21", "name": "Done", "to": {"name": "Done"}},
        ]
        mock_client.get_transitions.return_value = transitions

        result = get_transitions("PROJ-7")

        assert result == transitions

    def test_propagates_client_error(self, mock_client):
        """get_transitions lets JiraClient exceptions bubble up."""
        mock_client.get_transitions.side_effect = RuntimeError("Not found")

        with pytest.raises(RuntimeError):
            get_transitions("PROJ-7")


# ---------------------------------------------------------------------------
# transition_issue
# ---------------------------------------------------------------------------


class TestTransitionIssue:
    """Tests for the transition_issue tool."""

    def test_calls_client_with_key_and_transition_id(self, mock_client):
        """transition_issue forwards key and transition_id to client."""
        transition_issue("PROJ-3", "11")

        mock_client.transition_issue.assert_called_once_with("PROJ-3", "11")

    def test_returns_ok_status_with_key_and_transition_id(self, mock_client):
        """transition_issue returns confirmation dict."""
        result = transition_issue("PROJ-3", "21")

        assert result == {"status": "ok", "key": "PROJ-3", "transition_id": "21"}

    def test_propagates_client_error(self, mock_client):
        """transition_issue lets JiraClient exceptions bubble up."""
        mock_client.transition_issue.side_effect = ValueError(
            "Transition not available"
        )

        with pytest.raises(ValueError, match="Transition not available"):
            transition_issue("PROJ-3", "99")


# ---------------------------------------------------------------------------
# get_epics
# ---------------------------------------------------------------------------


class TestGetEpics:
    """Tests for the get_epics tool."""

    def test_passes_project_to_client(self, mock_client):
        """get_epics forwards the project key."""
        mock_client.get_epics.return_value = []

        get_epics("PROJ")

        mock_client.get_epics.assert_called_once_with("PROJ", max_results=50)

    def test_default_max_results_is_50(self, mock_client):
        """max_results defaults to 50."""
        mock_client.get_epics.return_value = []

        get_epics("PROJ")

        call_kwargs = mock_client.get_epics.call_args[1]
        assert call_kwargs["max_results"] == 50

    def test_custom_max_results(self, mock_client):
        """max_results is forwarded to client."""
        mock_client.get_epics.return_value = []

        get_epics("PROJ", max_results=10)

        call_kwargs = mock_client.get_epics.call_args[1]
        assert call_kwargs["max_results"] == 10

    def test_returns_epics_list(self, mock_client):
        """get_epics returns the list from the client."""
        epics = [
            {"key": "PROJ-100", "fields": {"summary": "Epic One"}},
            {"key": "PROJ-101", "fields": {"summary": "Epic Two"}},
        ]
        mock_client.get_epics.return_value = epics

        result = get_epics("PROJ")

        assert result == epics

    def test_propagates_client_error(self, mock_client):
        """get_epics lets JiraClient exceptions bubble up."""
        mock_client.get_epics.side_effect = RuntimeError("Project not found")

        with pytest.raises(RuntimeError, match="Project not found"):
            get_epics("BADKEY")


# ---------------------------------------------------------------------------
# get_issue_types
# ---------------------------------------------------------------------------


class TestGetIssueTypes:
    """Tests for the get_issue_types tool."""

    def test_passes_project_to_client(self, mock_client):
        """get_issue_types forwards the project key."""
        mock_client.get_issue_types.return_value = []

        get_issue_types("PROJ")

        mock_client.get_issue_types.assert_called_once_with("PROJ")

    def test_returns_issue_types_list(self, mock_client):
        """get_issue_types returns the list from the client."""
        types = [
            {"id": "1", "name": "Bug", "description": "A bug"},
            {"id": "2", "name": "Task", "description": "A task"},
            {"id": "3", "name": "Story", "description": "A story"},
        ]
        mock_client.get_issue_types.return_value = types

        result = get_issue_types("PROJ")

        assert result == types

    def test_propagates_client_error(self, mock_client):
        """get_issue_types lets JiraClient exceptions bubble up."""
        mock_client.get_issue_types.side_effect = PermissionError(
            "Access denied to project"
        )

        with pytest.raises(PermissionError, match="Access denied"):
            get_issue_types("PRIVATE")


# ---------------------------------------------------------------------------
# Client singleton laziness
# ---------------------------------------------------------------------------


class TestClientSingleton:
    """Tests for the lazy JiraClient singleton."""

    def test_client_is_initialised_lazily(self):
        """_client is None until the first tool call."""
        assert mcp_server_module._client is None

    def test_client_reused_across_calls(self):
        """The same client instance is reused between tool calls."""
        with patch.dict(
            "os.environ",
            {
                "JIRA_BASE_URL": "https://test.atlassian.net",
                "JIRA_USERNAME": "user@example.com",
                "JIRA_API_TOKEN": "token",
            },
        ), patch("temet_jira.mcp_server.JiraClient") as mock_client_cls:
            instance = MagicMock()
            instance.get_issue.return_value = {}
            instance.get_transitions.return_value = []
            mock_client_cls.return_value = instance

            get_issue("PROJ-1")
            get_transitions("PROJ-1")

            # JiraClient constructor called only once
            assert mock_client_cls.call_count == 1
