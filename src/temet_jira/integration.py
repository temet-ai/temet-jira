"""Jira integration utilities for creating epics and issues."""

import os
from typing import Any

from .client import JiraClient
from .formatter import (
    EpicBuilder,
    IssueBuilder,
    JiraDocumentBuilder,
    JiraFormatter,
    SubtaskBuilder,
    format_issue,
    format_issues_table,
)

__all__ = [
    "JiraClient",
    "JiraDocumentBuilder",
    "JiraFormatter",
    "EpicBuilder",
    "IssueBuilder",
    "SubtaskBuilder",
    "create_epic",
    "create_issue",
    "create_subtask",
    "format_issue",
    "format_issues_table",
]


def _get_default_epic_labels() -> list[str]:
    """Get default labels for epics from environment variables.

    Returns:
        List of default labels. Includes "epic" if custom labels are configured.
    """
    default_labels = os.environ.get("JIRA_DEFAULT_EPIC_LABELS", "")
    labels = [label.strip() for label in default_labels.split(",") if label.strip()]
    if labels:
        labels.append("epic")
    return labels


def _get_default_issue_labels() -> list[str]:
    """Get default labels for issues from environment variables.

    Returns:
        List of default labels.
    """
    default_labels = os.environ.get("JIRA_DEFAULT_ISSUE_LABELS", "")
    return [label.strip() for label in default_labels.split(",") if label.strip()]


def create_epic(
    client: JiraClient,
    project_key: str,
    title: str,
    priority: str,
    problem_statement: str,
    description: str,
    technical_requirements: list[str],
    acceptance_criteria: list[str],
    dependencies: str | None = None,
    services: str | None = None,
    code_example: str | None = None,
    code_language: str = "python",
    edge_cases: list[str] | None = None,
    test_cases: list[str] | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a Jira Epic with standardized format.

    Args:
        client: JiraClient instance
        project_key: Jira project key
        title: Epic title (without emoji)
        priority: Priority level (P0, P1, P2)
        problem_statement: Clear problem description
        description: Detailed solution description
        technical_requirements: List of implementation requirements
        acceptance_criteria: List of acceptance criteria
        dependencies: Optional dependencies (defaults to "None")
        services: Optional affected services (defaults to "TBD")
        code_example: Optional code example
        code_language: Language for code syntax highlighting
        edge_cases: Optional list of edge cases
        test_cases: Optional list of testing considerations
        labels: Optional additional labels

    Returns:
        Created epic data
    """
    # Build epic using the standardized builder
    epic = EpicBuilder(title, priority, dependencies, services)
    epic.add_problem_statement(problem_statement)
    epic.add_description(description)
    epic.add_technical_details(technical_requirements, code_example, code_language)
    epic.add_acceptance_criteria(acceptance_criteria)

    if edge_cases:
        epic.add_edge_cases(edge_cases)

    if test_cases:
        epic.add_testing_considerations(test_cases)

    # Build issue fields
    default_labels = _get_default_epic_labels()
    combined_labels = default_labels + (labels or [])
    fields = {
        "project": {"key": project_key},
        "summary": title,
        "issuetype": {"name": "Epic"},
        "description": epic.build(),
    }

    # Only include labels if there are any
    if combined_labels:
        fields["labels"] = combined_labels

    # Map priority
    priority_map = {"P0": "Highest", "P1": "High", "P2": "Medium", "P3": "Low"}
    if priority in priority_map:
        fields["priority"] = {"name": priority_map[priority]}

    return client.create_issue(fields)


def create_issue(
    client: JiraClient,
    project_key: str,
    title: str,
    component: str,
    description: str,
    implementation_details: list[str],
    acceptance_criteria: list[str],
    story_points: int | None = None,
    epic_key: str | None = None,
    issue_type: str = "Task",
    labels: list[str] | None = None,
    assignee_email: str | None = None,
) -> dict[str, Any]:
    """Create a Jira Issue/Task with standardized format.

    Args:
        client: JiraClient instance
        project_key: Jira project key
        title: Issue title (without emoji)
        component: Component name
        description: Clear description of what needs to be done
        implementation_details: List of implementation details
        acceptance_criteria: List of acceptance criteria
        story_points: Optional story points estimate
        epic_key: Optional parent epic key
        issue_type: Issue type (Task, Bug, Story, etc.)
        labels: Optional additional labels
        assignee_email: Optional assignee email

    Returns:
        Created issue data
    """
    # Build issue using the standardized builder
    issue = IssueBuilder(title, component, story_points, epic_key)
    issue.add_description(description)
    issue.add_implementation_details(implementation_details)
    issue.add_acceptance_criteria(acceptance_criteria)

    # Build issue fields
    default_labels = _get_default_issue_labels()
    combined_labels = default_labels + (labels or [])
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": title,
        "issuetype": {"name": issue_type},
        "description": issue.build(),
    }

    # Only include labels if there are any
    if combined_labels:
        fields["labels"] = combined_labels

    # Add component if it exists
    fields["components"] = [{"name": component}]

    # Add assignee if provided
    if assignee_email:
        fields["assignee"] = {"emailAddress": assignee_email}

    # Link to epic if available
    if epic_key:
        epic_link_field = client.get_epic_link_field()
        if epic_link_field:
            fields[epic_link_field] = epic_key

    return client.create_issue(fields)


def create_subtask(
    client: JiraClient,
    project_key: str,
    parent_key: str,
    title: str,
    description: str,
    steps: list[str] | None = None,
    done_criteria: list[str] | None = None,
    estimated_hours: float | None = None,
    assignee_email: str | None = None,
) -> dict[str, Any]:
    """Create a Jira Subtask with standardized format.

    Args:
        client: JiraClient instance
        project_key: Jira project key
        parent_key: Parent issue key (e.g., "PROJ-456")
        title: Subtask title (without emoji)
        description: Brief description of the subtask
        steps: Optional list of implementation steps
        done_criteria: Optional definition of done criteria
        estimated_hours: Optional time estimate in hours
        assignee_email: Optional assignee email

    Returns:
        Created subtask data
    """
    # Build subtask using the standardized builder
    subtask = SubtaskBuilder(title, parent_key, estimated_hours)
    subtask.add_description(description)

    if steps:
        subtask.add_steps(steps)

    if done_criteria:
        subtask.add_done_criteria(done_criteria)

    # Build issue fields
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "parent": {"key": parent_key},
        "summary": title,
        "issuetype": {"name": "Sub-task"},
        "description": subtask.build(),
    }

    # Add assignee if provided
    if assignee_email:
        fields["assignee"] = {"emailAddress": assignee_email}

    return client.create_issue(fields)
