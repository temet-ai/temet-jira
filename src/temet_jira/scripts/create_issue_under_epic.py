#!/usr/bin/env python3
"""
Script to create a Jira issue under an epic.

Usage:
    python create_issue_under_epic.py --epic PROJ-470 --summary "Your summary" --description "Optional description" --project PROJ

Note: Configure JIRA_DEFAULT_PROJECT environment variable to set a default project key.
"""

import argparse
import os
import sys
from typing import Any

from temet_jira.client import JiraClient
from temet_jira.document import DocumentBuilder


def create_issue_under_epic(
    epic_key: str,
    summary: str,
    description: str | None = None,
    issue_type: str = "Task",
    project_key: str | None = None,
) -> str | None:
    """Create a new issue under the specified epic using the JiraClient."""
    try:
        client = JiraClient()

        # Use provided project key or fall back to environment variable
        resolved_project_key = project_key or os.environ.get("JIRA_DEFAULT_PROJECT")

        if not resolved_project_key:
            print(
                "Error: Project key must be provided via --project or JIRA_DEFAULT_PROJECT environment variable"
            )
            sys.exit(1)

        # Build issue fields
        fields: dict[str, Any] = {
            "project": {"key": resolved_project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }

        # Add description as ADF if provided
        if description:
            builder = DocumentBuilder()
            builder.paragraph(description)
            fields["description"] = builder.build()

        # Link to epic
        epic_link_field = client.get_epic_link_field()
        if epic_link_field:
            fields[epic_link_field] = epic_key

        print(f"Creating {issue_type}...")
        result = client.create_issue(fields)

        issue_key = result.get("key")
        if issue_key:
            print(f"✓ Created issue: {issue_key}")
            print(f"✓ Successfully linked {issue_key} to epic {epic_key}")
            print(f"\nView the issue at: {client.base_url}/browse/{issue_key}")
            return str(issue_key)
        else:
            print("Error: No issue key returned")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a Jira issue under an epic",
    )
    parser.add_argument("--epic", "-e", required=True, help="Epic key (e.g., PROJ-470)")
    parser.add_argument("--summary", "-s", required=True, help="Issue summary")
    parser.add_argument("--description", "-d", help="Issue description (optional)")
    parser.add_argument(
        "--type", "-t", default="Task", help="Issue type (default: Task)"
    )
    parser.add_argument(
        "--project",
        "-p",
        help="Project key (or set JIRA_DEFAULT_PROJECT environment variable)",
    )

    args = parser.parse_args()

    create_issue_under_epic(
        epic_key=args.epic,
        summary=args.summary,
        description=args.description,
        issue_type=args.type,
        project_key=args.project,
    )


if __name__ == "__main__":
    main()
