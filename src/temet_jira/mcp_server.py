"""FastMCP server exposing JiraClient methods as MCP tools.

This module wraps core JiraClient operations as MCP tools for use by
AI agents over the stdio JSON-RPC transport. All output is structured
JSON — no Rich formatting. Logging goes to stderr only.

Usage:
    Run via the ``temet-jira-mcp`` entry point (defined in pyproject.toml).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from fastmcp import FastMCP

from temet_jira.client import JiraClient

# ---------------------------------------------------------------------------
# Logging — stderr only so stdout stays clean for JSON-RPC
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("temet_jira.mcp_server")

# ---------------------------------------------------------------------------
# FastMCP app
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "temet-jira",
    instructions="Jira Cloud MCP server — search, create, update, and manage issues",
)

# ---------------------------------------------------------------------------
# Lazy-initialised JiraClient singleton
# ---------------------------------------------------------------------------
_client: JiraClient | None = None


def _get_client() -> JiraClient:
    """Return (and lazily create) the shared JiraClient instance.

    Credentials are resolved via the standard chain:
    env vars -> ``~/.config/temet-jira/config.yaml``.
    """
    global _client  # noqa: PLW0603
    if _client is None:
        logger.info("Initialising JiraClient (first tool call)")
        _client = JiraClient()
    return _client


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_issue(
    key: str,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch a single Jira issue by key.

    Args:
        key: Jira issue key (e.g. PROJ-123).
        expand: Optional fields to expand (e.g. ['transitions', 'changelog']).

    Returns:
        Full issue payload as a dict.
    """
    client = _get_client()
    return client.get_issue(key, expand=expand)


@mcp.tool()
def search_issues(
    jql: str,
    max_results: int = 50,
    fields: list[str] | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Search for Jira issues using JQL.

    Args:
        jql: JQL query string.
        max_results: Maximum number of results to return (default 50).
        fields: Specific fields to include in results.
        expand: Fields to expand (e.g. ['changelog']).

    Returns:
        Dict with ``issues`` list and ``is_last`` pagination flag.
    """
    client = _get_client()
    issues, is_last = client.search_issues(
        jql=jql,
        fields=fields,
        max_results=max_results,
        expand=expand,
    )
    return {"issues": issues, "is_last": is_last}


@mcp.tool()
def create_issue(
    project: str,
    summary: str,
    issue_type: str = "Task",
    description: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    assignee_id: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new Jira issue.

    Args:
        project: Project key (e.g. PROJ).
        summary: Issue summary / title.
        issue_type: Issue type name (default "Task").
        description: Plain-text description (converted to simple ADF).
        priority: Priority name (e.g. "High").
        labels: List of label strings.
        assignee_id: Atlassian account ID of the assignee.
        extra_fields: Any additional fields to set on the issue.

    Returns:
        Created issue data (includes key, id, self).
    """
    fields: dict[str, Any] = {
        "project": {"key": project},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }

    if description is not None:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ],
        }

    if priority is not None:
        fields["priority"] = {"name": priority}

    if labels is not None:
        fields["labels"] = labels

    if assignee_id is not None:
        fields["assignee"] = {"accountId": assignee_id}

    if extra_fields:
        fields.update(extra_fields)

    client = _get_client()
    return client.create_issue(fields)


@mcp.tool()
def update_issue(
    key: str,
    fields: dict[str, Any],
) -> dict[str, str]:
    """Update fields on an existing Jira issue.

    Args:
        key: Jira issue key (e.g. PROJ-123).
        fields: Dict of field names/values to update.

    Returns:
        Confirmation dict with the updated issue key.
    """
    client = _get_client()
    client.update_issue(key, fields)
    return {"status": "ok", "key": key}


@mcp.tool()
def add_comment(
    key: str,
    body: str,
) -> dict[str, Any]:
    """Add a plain-text comment to a Jira issue.

    The text is automatically wrapped in Atlassian Document Format.

    Args:
        key: Jira issue key (e.g. PROJ-123).
        body: Comment text (plain text).

    Returns:
        Created comment data from Jira.
    """
    adf_body: dict[str, Any] = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": body}],
            }
        ],
    }
    client = _get_client()
    return client.add_comment(key, adf_body)


@mcp.tool()
def get_transitions(
    key: str,
) -> list[dict[str, Any]]:
    """List available workflow transitions for a Jira issue.

    Args:
        key: Jira issue key (e.g. PROJ-123).

    Returns:
        List of transition dicts (id, name, to status, etc.).
    """
    client = _get_client()
    return client.get_transitions(key)


@mcp.tool()
def transition_issue(
    key: str,
    transition_id: str,
) -> dict[str, str]:
    """Execute a workflow transition on a Jira issue.

    Use ``get_transitions`` first to discover valid transition IDs.

    Args:
        key: Jira issue key (e.g. PROJ-123).
        transition_id: ID of the transition to execute.

    Returns:
        Confirmation dict with the transitioned issue key.
    """
    client = _get_client()
    client.transition_issue(key, transition_id)
    return {"status": "ok", "key": key, "transition_id": transition_id}


@mcp.tool()
def get_epics(
    project: str,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List epics in a Jira project.

    Args:
        project: Project key (e.g. PROJ).
        max_results: Maximum number of epics to return (default 50).

    Returns:
        List of epic issue dicts.
    """
    client = _get_client()
    return client.get_epics(project, max_results=max_results)


@mcp.tool()
def get_issue_types(
    project: str,
) -> list[dict[str, Any]]:
    """List available issue types for a Jira project.

    Args:
        project: Project key (e.g. PROJ).

    Returns:
        List of issue type dicts (id, name, description, etc.).
    """
    client = _get_client()
    return client.get_issue_types(project)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server over stdio."""
    logger.info("Starting temet-jira MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
