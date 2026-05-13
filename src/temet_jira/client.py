"""Jira API client for Jira Cloud instances."""

import os
from base64 import b64encode
from typing import Any, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import get_value


def _get_default_max_results() -> int:
    """Get default max results from config or environment variable.

    Returns:
        Default maximum results per page (defaults to 300)
    """
    try:
        value = get_value("max_results")
        return int(value) if value else 300
    except ValueError:
        return 300


class JiraClient:
    """Client for interacting with Jira REST API v3."""

    base_url: str
    username: str
    api_token: str

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize Jira client with credentials and configuration.

        Credentials are resolved in this order:
        1. Explicit arguments passed to __init__
        2. Environment variables (JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN)
        3. Config file (~/.config/temet-jira/config.yaml)

        Args:
            base_url: Jira instance URL
            username: Jira username/email
            api_token: Jira API token
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        resolved_base_url = base_url or get_value("base_url")
        resolved_username = username or get_value("username")
        resolved_api_token = api_token or get_value("api_token")
        self.timeout = timeout

        if not resolved_base_url:
            raise ValueError(
                "Jira URL not configured. Run 'temet-jira setup' or set JIRA_BASE_URL"
            )
        if not resolved_username or not resolved_api_token:
            raise ValueError(
                "Jira credentials not configured. Run 'temet-jira setup' or set JIRA_USERNAME and JIRA_API_TOKEN"
            )

        self.base_url = resolved_base_url
        self.username = resolved_username
        self.api_token = resolved_api_token

        # Setup authentication
        credentials = f"{self.username}:{self.api_token}"
        self.auth_header = b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)

    @property
    def server_url(self) -> str:
        """Get the base server URL without trailing slash.

        Returns:
            Base server URL
        """
        return self.base_url.rstrip("/")

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Make an HTTP request with proper error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL to request
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def get_issue(
        self, issue_key: str, expand: list[str] | None = None
    ) -> dict[str, Any]:
        """Fetch a Jira issue by key.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            expand: List of fields to expand (e.g., ['transitions', 'changelog'])

        Returns:
            Issue data as dictionary
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        response = self._request("GET", url, params=params)
        return cast(dict[str, Any], response.json())

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Create a new Jira issue.

        Args:
            fields: Issue fields dictionary containing project, summary, issuetype, etc.

        Returns:
            Created issue data
        """
        url = f"{self.base_url}/rest/api/3/issue"
        data = {"fields": fields}

        response = self._request("POST", url, json=data)
        return cast(dict[str, Any], response.json())

    def update_issue(self, issue_key: str, fields: dict[str, Any]) -> None:
        """Update a Jira issue.

        Args:
            issue_key: Jira issue key
            fields: Fields to update
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        data = {"fields": fields}

        self._request("PUT", url, json=data)

    def add_comment(self, issue_key: str, body: dict[str, Any]) -> dict[str, Any]:
        """Add a comment to a Jira issue.

        Args:
            issue_key: Jira issue key
            body: Comment body in ADF format

        Returns:
            Created comment data
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        data = {"body": body}

        response = self._request("POST", url, json=data)
        return cast(dict[str, Any], response.json())

    def get_comments(
        self,
        issue_key: str,
        max_results: int = 50,
        order_by: str = "-created",
    ) -> list[dict[str, Any]]:
        """Fetch comments for a Jira issue.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            max_results: Maximum number of comments to return (default 50)
            order_by: Sort order — '-created' (newest first) or '+created' (oldest first)

        Returns:
            List of comment dicts from the Jira API
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        params: dict[str, Any] = {
            "maxResults": max_results,
            "orderBy": order_by,
        }
        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())
        return cast(list[dict[str, Any]], data.get("comments", []))

    def get_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """Get available transitions for an issue.

        Args:
            issue_key: Jira issue key

        Returns:
            List of available transitions
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        response = self._request("GET", url)
        data = cast(dict[str, Any], response.json())
        return cast(list[dict[str, Any]], data.get("transitions", []))

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: dict[str, Any] | None = None,
    ) -> None:
        """Transition an issue to a new status.

        Args:
            issue_key: Jira issue key
            transition_id: ID of the transition
            fields: Optional fields to update during transition
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        data = {"transition": {"id": transition_id}}
        if fields:
            data["fields"] = fields

        self._request("POST", url, json=data)

    def search_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        _start_at: int = 0,
        max_results: int | None = None,
        expand: list[str] | None = None,
        page_token: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Search for issues using JQL.

        Args:
            jql: Jira Query Language string
            fields: List of fields to return (defaults to all fields if not specified)
            _start_at: Starting index for pagination (DEPRECATED - kept for backward compatibility but not used)
            max_results: Maximum number of results per page (defaults to JIRA_DEFAULT_MAX_RESULTS env var)
            expand: List of fields to expand (e.g., ['changelog', 'transitions'])
            page_token: Pagination token from previous response (new pagination mechanism)

        Returns:
            Tuple of (issues, is_last)
            - issues: List of issues matching the search
            - is_last: Whether this is the last page of results

        Note:
            The new /rest/api/3/search/jql endpoint uses token-based pagination.
            To get the next page, use the nextPageToken from the response.
            The start_at parameter is ignored by this API.
        """
        if max_results is None:
            max_results = _get_default_max_results()

        url = f"{self.base_url}/rest/api/3/search/jql"
        params = {"jql": jql, "maxResults": max_results}

        # If fields are specified, use them; otherwise request common fields
        if fields:
            params["fields"] = ",".join(fields)
        else:
            # Default to common fields to ensure we get useful data
            params["fields"] = (
                "key,summary,status,assignee,priority,issuetype,created,updated,description,labels"
            )

        if expand:
            params["expand"] = ",".join(expand)

        if page_token:
            params["nextPageToken"] = page_token

        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())

        issues = cast(list[dict[str, Any]], data.get("issues", []))
        is_last = bool(data.get("isLast", True))

        return issues, is_last

    def search_issues_paginated(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int | None = None,
        expand: list[str] | None = None,
        page_token: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Search for issues using JQL with pagination support.

        Args:
            jql: Jira Query Language string
            fields: List of fields to return (defaults to all fields if not specified)
            max_results: Maximum number of results per page (defaults to JIRA_DEFAULT_MAX_RESULTS env var)
            expand: List of fields to expand (e.g., ['changelog', 'transitions'])
            page_token: Pagination token from previous response (for next page)

        Returns:
            Tuple of (issues, next_page_token, is_last)
            - issues: List of issues matching the search
            - next_page_token: Token for next page (None if no more pages)
            - is_last: Whether this is the last page
        """
        if max_results is None:
            max_results = _get_default_max_results()

        url = f"{self.base_url}/rest/api/3/search/jql"
        params = {"jql": jql, "maxResults": max_results}

        # If fields are specified, use them; otherwise request common fields
        if fields:
            params["fields"] = ",".join(fields)
        else:
            # Default to common fields to ensure we get useful data
            params["fields"] = (
                "key,summary,status,assignee,priority,issuetype,created,updated,description,labels"
            )

        if expand:
            params["expand"] = ",".join(expand)

        if page_token:
            params["nextPageToken"] = page_token

        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())

        issues = cast(list[dict[str, Any]], data.get("issues", []))
        next_token = cast(str | None, data.get("nextPageToken"))
        is_last = bool(data.get("isLast", False))

        return issues, next_token, is_last

    def search_all_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        expand: list[str] | None = None,
        max_per_page: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search for all issues matching JQL using token-based pagination.

        Args:
            jql: Jira Query Language string
            fields: List of fields to return (defaults to all fields if not specified)
            expand: List of fields to expand (e.g., ['changelog', 'transitions'])
            max_per_page: Maximum number of results per page (defaults to JIRA_DEFAULT_MAX_RESULTS env var)

        Returns:
            List of all issues matching the search
        """
        if max_per_page is None:
            max_per_page = _get_default_max_results()

        all_issues = []
        page_token = None
        is_last = False

        while not is_last:
            issues, page_token, is_last = self.search_issues_paginated(
                jql=jql,
                fields=fields,
                max_results=max_per_page,
                expand=expand,
                page_token=page_token,
            )

            if not issues:
                break

            all_issues.extend(issues)

        return all_issues

    def get_projects(self, recent: int = 20) -> list[dict[str, Any]]:
        """Get list of projects.

        Args:
            recent: Number of recent projects to return

        Returns:
            List of project data
        """
        url = f"{self.base_url}/rest/api/3/project"
        params = {"recent": recent}

        response = self._request("GET", url, params=params)
        return cast(list[dict[str, Any]], response.json())

    def get_project(self, project_key: str) -> dict[str, Any]:
        """Get project details.

        Args:
            project_key: Project key

        Returns:
            Project data
        """
        url = f"{self.base_url}/rest/api/3/project/{project_key}"
        response = self._request("GET", url)
        return cast(dict[str, Any], response.json())

    def get_fields(self) -> list[dict[str, Any]]:
        """Get all field definitions.

        Returns:
            List of field definitions
        """
        url = f"{self.base_url}/rest/api/3/field"
        response = self._request("GET", url)
        return cast(list[dict[str, Any]], response.json())

    def get_custom_field_id(self, field_name: str) -> str | None:
        """Get custom field ID by name.

        Args:
            field_name: Name of the custom field

        Returns:
            Field ID if found, None otherwise
        """
        fields = self.get_fields()
        for field in fields:
            if field.get("name") == field_name:
                return str(field["id"])
        return None

    def get_epic_link_field(self) -> str | None:
        """Get the custom field ID for epic link.

        Returns:
            Epic link field ID if found
        """
        # Try standard name first
        epic_field = self.get_custom_field_id("Epic Link")
        if epic_field:
            return epic_field

        # Try common field IDs (including M&S specific)
        common_ids = [
            "customfield_11923",
            "customfield_10014",
            "customfield_10008",
            "customfield_10011",
        ]
        fields = self.get_fields()
        field_ids = {field["id"] for field in fields}

        for field_id in common_ids:
            if field_id in field_ids:
                return field_id

        return None

    def get_epics(
        self, project_key: str, max_results: int | None = None
    ) -> list[dict[str, Any]]:
        """Get epics for a project.

        Args:
            project_key: Project key
            max_results: Maximum number of epics to return (defaults to JIRA_DEFAULT_MAX_RESULTS env var)

        Returns:
            List of epic issues
        """
        jql = f"project = {project_key} AND issuetype = Epic ORDER BY created DESC"
        issues, _ = self.search_issues(jql, max_results=max_results)
        return issues

    def get_issue_types(self, project_key: str) -> list[dict[str, Any]]:
        """Get available issue types for a project.

        Uses the new createmeta/{project}/issuetypes endpoint first,
        falls back to the deprecated createmeta endpoint if unavailable.

        Args:
            project_key: Project key

        Returns:
            List of issue types
        """
        # Try new endpoint first
        try:
            url = f"{self.base_url}/rest/api/3/issue/createmeta/{project_key}/issuetypes"
            response = self._request("GET", url)
            data = cast(dict[str, Any], response.json())
            return cast(list[dict[str, Any]], data.get("issueTypes", data.get("values", [])))
        except requests.exceptions.HTTPError:
            pass

        # Fallback to deprecated endpoint
        url = f"{self.base_url}/rest/api/3/issue/createmeta"
        params = {"projectKeys": project_key, "expand": "projects.issuetypes.fields"}

        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())

        projects = data.get("projects")
        if projects and isinstance(projects, list) and len(projects) > 0:
            project = cast(dict[str, Any], projects[0])
            return cast(list[dict[str, Any]], project.get("issuetypes", []))
        return []

    def get_priorities(self) -> list[dict[str, Any]]:
        """Get available priorities.

        Returns:
            List of priorities
        """
        url = f"{self.base_url}/rest/api/3/priority"
        response = self._request("GET", url)
        return cast(list[dict[str, Any]], response.json())

    def get_statuses(self) -> list[dict[str, Any]]:
        """Get all statuses.

        Returns:
            List of statuses
        """
        url = f"{self.base_url}/rest/api/3/status"
        response = self._request("GET", url)
        return cast(list[dict[str, Any]], response.json())

    def get_users_assignable(
        self,
        project_key: str,
        issue_key: str | None = None,
        query: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get users assignable to issues in a project.

        Args:
            project_key: Project key
            issue_key: Optional issue key for more specific results
            query: Optional search query
            max_results: Maximum number of results (defaults to JIRA_DEFAULT_MAX_RESULTS env var)

        Returns:
            List of assignable users
        """
        if max_results is None:
            max_results = _get_default_max_results()

        url = f"{self.base_url}/rest/api/3/user/assignable/search"
        params = {"project": project_key, "maxResults": max_results}
        if issue_key:
            params["issueKey"] = issue_key
        if query:
            params["query"] = query

        response = self._request("GET", url, params=params)
        return cast(list[dict[str, Any]], response.json())

    def add_attachment(
        self, issue_key: str, file_path: str, file_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Add an attachment to an issue.

        Args:
            issue_key: Jira issue key
            file_path: Path to file to attach
            file_name: Optional custom filename

        Returns:
            List of attachment data
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"

        # Temporarily remove Content-Type for multipart upload
        headers = dict(self.session.headers)
        del headers["Content-Type"]
        headers["X-Atlassian-Token"] = "no-check"

        with open(file_path, "rb") as f:
            files = {"file": (file_name or os.path.basename(file_path), f)}
            response = self._request("POST", url, files=files, headers=headers)

        return cast(list[dict[str, Any]], response.json())

    def delete_issue(self, issue_key: str) -> None:
        """Delete an issue.

        Args:
            issue_key: Jira issue key
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        self._request("DELETE", url)

    def get_server_info(self) -> dict[str, Any]:
        """Get Jira server/instance information.

        Returns:
            Server information
        """
        url = f"{self.base_url}/rest/api/3/serverInfo"
        response = self._request("GET", url)
        return cast(dict[str, Any], response.json())

    def get_myself(self) -> dict[str, Any]:
        """Get current user information.

        Returns:
            Current user data
        """
        url = f"{self.base_url}/rest/api/3/myself"
        response = self._request("GET", url)
        return cast(dict[str, Any], response.json())

    def get_boards(self, project_key: str | None = None) -> list[dict[str, Any]]:
        """Get boards, optionally filtered by project.

        Returns:
            List of board objects
        """
        url = f"{self.base_url}/rest/agile/1.0/board"
        params: dict[str, Any] = {"maxResults": 50}
        if project_key:
            params["projectKeyOrId"] = project_key
        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())
        return cast(list[dict[str, Any]], data.get("values", []))

    def get_active_sprint(self, board_id: int) -> dict[str, Any] | None:
        """Get the active sprint for a board.

        Returns:
            Active sprint object or None if no active sprint
        """
        url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint"
        params = {"state": "active"}
        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())
        sprints = cast(list[dict[str, Any]], data.get("values", []))
        return sprints[0] if sprints else None

    def get_backlog_count(self, board_id: int) -> int:
        """Get the number of issues in a board's backlog.

        Returns:
            Count of backlog issues
        """
        url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/backlog"
        params = {"maxResults": 0}
        response = self._request("GET", url, params=params)
        data = cast(dict[str, Any], response.json())
        return cast(int, data.get("total", 0))

    def get_components(self, project_key: str) -> list[dict[str, Any]]:
        """Get components for a project.

        Returns:
            List of component objects with id, name, description
        """
        url = f"{self.base_url}/rest/api/3/project/{project_key}/components"
        response = self._request("GET", url)
        return cast(list[dict[str, Any]], response.json())

    def get_labels_used(self, project_key: str, max_issues: int = 100) -> list[str]:
        """Get labels actually used in a project by sampling recent issues.

        Returns:
            Sorted list of unique label strings
        """
        jql = f"project = {project_key} AND labels is not EMPTY ORDER BY updated DESC"
        issues, _ = self.search_issues(jql, fields=["labels"], max_results=max_issues)
        seen: set[str] = set()
        for issue in issues:
            fields = issue.get("fields") or {}
            for label in fields.get("labels") or []:
                if label:
                    seen.add(label)
        return sorted(seen)
