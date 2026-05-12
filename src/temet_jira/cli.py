"""Jira CLI commands."""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from .analysis.formatters import format_as_csv, format_as_json, format_as_jsonl
from .analysis.state_analyzer import StateDurationAnalyzer
from .client import JiraClient
from .config import (
    VALID_KEYS,
    config_exists,
    delete_value,
    get_all_config,
    get_config_path,
    get_value,
    is_configured,
    mask_sensitive,
    set_value,
)
from .document import DocumentBuilder, TypedBuilder
from .formatter import format_issue, format_issues_table

# Load environment variables from .env file
load_dotenv()

console = Console()


def _get_default_max_results() -> int:
    """Get default max results from environment variable.

    Returns:
        Default maximum results per page (from JIRA_DEFAULT_MAX_RESULTS env var, defaults to 300)
    """
    try:
        return int(os.environ.get("JIRA_DEFAULT_MAX_RESULTS", "300"))
    except ValueError:
        return 300


_SECTIONS: dict[str, list[str]] = {
    "Configuration": ["setup", "config"],
    "Reading": ["get", "search", "types"],
    "Epics": ["epics", "epic-details"],
    "Creating & Editing": ["create", "update", "comment", "transitions"],
    "Data & Analysis": ["export", "analyze"],
    "Integrations": ["mcp"],
}

_CMD_TO_SECTION: dict[str, str] = {
    cmd: section for section, cmds in _SECTIONS.items() for cmd in cmds
}


class _SectionedGroup(click.Group):
    """click.Group that displays commands grouped into labelled sections."""

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        sections: dict[str, list[tuple[str, str]]] = {s: [] for s in _SECTIONS}
        sections["Other"] = []

        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            help_text = cmd.get_short_help_str(limit=formatter.width or 80)
            bucket = _CMD_TO_SECTION.get(name, "Other")
            if bucket not in sections:
                sections[bucket] = []
            sections[bucket].append((name, help_text))

        for section_name, rows in sections.items():
            if not rows:
                continue
            with formatter.section(section_name):
                formatter.write_dl(rows)


@click.group(name="jira", cls=_SectionedGroup)
def jira() -> None:
    """Jira integration commands."""
    pass


@jira.command()
@click.argument("issue_key")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "jsonl", "table"], case_sensitive=False),
    default="table",
    help="Output format (json|jsonl|table) — default: table",
)
@click.option("--output", "-o", help="Output file path (optional)")
@click.option(
    "--expand",
    help="Expand fields like changelog, transitions (comma-separated)",
)
@click.option(
    "--comments",
    is_flag=True,
    default=False,
    help="Fetch and display comments for the issue",
)
@click.option(
    "--fields",
    type=click.Choice(["standard", "all"], case_sensitive=False),
    default="standard",
    help="Field set to display: standard (default) or all (includes Other Fields)",
)
def get(
    issue_key: str,
    output_format: str,
    output: str | None,
    expand: str | None,
    comments: bool,
    fields: str,
) -> None:
    """Get details of a Jira issue."""
    try:
        client = JiraClient()

        # Parse expand options — always include "names" for human-readable field labels
        expand_list = (
            [e.strip() for e in expand.split(",")]
            if expand and expand.strip()
            else []
        )
        if "names" not in expand_list:
            expand_list.append("names")

        with console.status(f"Fetching issue {issue_key}..."):
            issue = client.get_issue(issue_key, expand=expand_list)

        # Fetch comments if requested
        comment_list: list[dict[str, Any]] | None = None
        if comments:
            with console.status(f"Fetching comments for {issue_key}..."):
                comment_list = client.get_comments(issue_key)

        # Handle output format
        if output_format == "json":
            formatted = format_as_json([issue])
            if output:
                Path(output).write_text(formatted)
                console.print(f"[green]✓[/green] Issue saved to {output}")
            else:
                click.echo(formatted)
        elif output_format == "jsonl":
            formatted = format_as_jsonl([issue])
            if output:
                Path(output).write_text(formatted)
                console.print(f"[green]✓[/green] Issue saved to {output}")
            else:
                click.echo(formatted)
        else:  # table (default)
            format_issue(issue, comments=comment_list, show_all_fields=(fields == "all"))
            if output:
                console.print(
                    "[yellow]Note: Table format cannot be saved to file. "
                    "Use --format json or --format jsonl for file output.[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
@click.option("--summary", help="Update issue summary")
@click.option(
    "--description", help="Update issue description (plain text, will be formatted)"
)
@click.option(
    "--description-adf",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to JSON file containing ADF document for description",
)
@click.option("--assignee", help="Update assignee (use email or account ID)")
@click.option(
    "--priority", help="Update priority (e.g., Highest, High, Medium, Low, Lowest)"
)
@click.option("--labels", help="Update labels (comma-separated)")
@click.option("--status", help="Transition to status (e.g., In Progress, Done)")
def update(
    issue_key: str,
    summary: str | None,
    description: str | None,
    description_adf: Path | None,
    assignee: str | None,
    priority: str | None,
    labels: str | None,
    status: str | None,
) -> None:
    """Update a Jira issue.

    For rich description formatting, use --description-adf with a JSON file
    containing valid Atlassian Document Format (ADF).
    """
    try:
        client = JiraClient()

        # Validate mutually exclusive options
        if description and description_adf:
            console.print(
                "[red]Error:[/red] Cannot use both --description and --description-adf"
            )
            raise click.Abort()

        # Build update fields
        fields: dict[str, Any] = {}

        if summary:
            fields["summary"] = summary

        if description_adf:
            # Load raw ADF from JSON file
            try:
                adf_content = json.loads(description_adf.read_text())
                # Validate basic ADF structure
                if (
                    not isinstance(adf_content, dict)
                    or adf_content.get("type") != "doc"
                ):
                    console.print(
                        "[red]Error:[/red] Invalid ADF format. Must be a JSON object with 'type': 'doc'"
                    )
                    raise click.Abort()
                fields["description"] = adf_content
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in ADF file: {e}")
                raise click.Abort() from e
        elif description:
            # Use DocumentBuilder for proper ADF format
            builder = DocumentBuilder()
            builder.paragraph(description)
            fields["description"] = builder.build()

        if assignee:
            # For cloud Jira, we need account ID, not email
            # This is a simplified version - in production you'd want to search for users
            if "@" in assignee:
                console.print(
                    "[yellow]Note: Assignee should be an account ID, not email. Attempting anyway...[/yellow]"
                )
            fields["assignee"] = (
                {"accountId": assignee}
                if "@" not in assignee
                else {"emailAddress": assignee}
            )

        if priority:
            fields["priority"] = {"name": priority}

        if labels is not None:
            fields["labels"] = labels.split(",") if labels else []

        # Update fields if any provided
        if fields:
            with console.status(f"Updating issue {issue_key}..."):
                client.update_issue(issue_key, fields)
            console.print(f"[green]✓[/green] Issue {issue_key} updated successfully")

        # Handle status transition separately
        if status:
            with console.status("Getting available transitions..."):
                transitions = client.get_transitions(issue_key)

            # Find matching transition
            transition = None
            for t in transitions:
                if t["name"].lower() == status.lower():
                    transition = t
                    break

            if transition:
                with console.status(f"Transitioning to {status}..."):
                    client.transition_issue(issue_key, transition["id"])
                console.print(f"[green]✓[/green] Status changed to {status}")
            else:
                available = ", ".join([t["name"] for t in transitions])
                console.print(
                    f"[yellow]Status '{status}' not available. Available transitions: {available}[/yellow]"
                )

        # Show updated issue
        if fields or status:
            console.print("\n[bold]Updated issue:[/bold]")
            issue = client.get_issue(issue_key)
            format_issue(issue)
        else:
            console.print("[yellow]No updates specified[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
@click.option("--message", "-m", help="Comment message (will prompt if not provided)")
@click.option(
    "--adf",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to JSON file containing ADF document for comment body",
)
def comment(issue_key: str, message: str | None, adf: Path | None) -> None:
    """Add a comment to a Jira issue.

    For rich comment formatting, use --adf with a JSON file
    containing valid Atlassian Document Format (ADF).
    """
    try:
        client = JiraClient()

        # Validate mutually exclusive options
        if message and adf:
            console.print("[red]Error:[/red] Cannot use both --message and --adf")
            raise click.Abort()

        if adf:
            # Load raw ADF from JSON file
            try:
                adf_body = json.loads(adf.read_text())
                # Validate basic ADF structure
                if not isinstance(adf_body, dict) or adf_body.get("type") != "doc":
                    console.print(
                        "[red]Error:[/red] Invalid ADF format. Must be a JSON object with 'type': 'doc'"
                    )
                    raise click.Abort()
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in ADF file: {e}")
                raise click.Abort() from e
        else:
            # Get comment text
            if not message:
                message = Prompt.ask("Enter comment")
                if not message:
                    console.print("[yellow]No comment provided[/yellow]")
                    return

            # Convert plain text to proper ADF format
            builder = DocumentBuilder()
            builder.paragraph(message)
            adf_body = builder.build()

        with console.status(f"Adding comment to {issue_key}..."):
            result = client.add_comment(issue_key, adf_body)

        console.print("[green]✓[/green] Comment added successfully")
        console.print(f"Comment ID: {result['id']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("jql")
@click.option(
    "--max-results",
    "-n",
    default=None,
    type=int,
    help=f"Maximum number of results (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()})",
)
@click.option("--fields", help="Select specific fields to return (comma-separated)")
@click.option(
    "--expand", help="Expand fields like changelog, transitions (comma-separated)"
)
@click.option("--output", "-o", help="Output file path (optional)")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "csv", "jsonl", "table"], case_sensitive=False),
    default="table",
    help="Output format (json|csv|jsonl|table) - default: table",
)
@click.option(
    "--all", "fetch_all", is_flag=True, help="Fetch all results (bypass limit)"
)
def search(
    jql: str,
    max_results: int,
    fields: str | None,
    expand: str | None,
    output: str | None,
    output_format: str,
    fetch_all: bool,
) -> None:
    """Search for issues using JQL."""
    from pathlib import Path

    try:
        client = JiraClient()

        # Parse comma-separated fields and expand options
        fields_list = (
            [f.strip() for f in fields.split(",")]
            if fields and fields.strip()
            else None
        )
        expand_list = (
            [e.strip() for e in expand.split(",")]
            if expand and expand.strip()
            else None
        )

        # Handle --all option for fetching all results
        if fetch_all:
            with console.status("Fetching all issues..."):
                # When using --all, ignore --max-results and use default page size
                issues = client.search_all_issues(
                    jql, fields=fields_list, expand=expand_list, max_per_page=None
                )
            console.print(f"[green]✓[/green] Fetched {len(issues)} issue(s) total")
        else:
            with console.status("Searching issues..."):
                issues, is_last = client.search_issues(
                    jql, max_results=max_results, fields=fields_list, expand=expand_list
                )

            # Warn if results are truncated (only for interactive/table output)
            if output_format == "table" or output:
                if not is_last:
                    console.print(
                        f"[yellow]⚠️  Retrieved {len(issues)} results (more available)[/yellow]"
                    )
                    console.print(
                        "[yellow]   To get all results: Add --all flag to this command[/yellow]\n"
                    )
                else:
                    console.print(f"[green]✓[/green] Fetched {len(issues)} issue(s)")

        if not issues:
            console.print("[yellow]No issues found[/yellow]")
            return

        # Format output based on format option
        if output_format == "json":
            try:
                # Use the new JSON formatter from formatters module
                formatted_output = format_as_json(issues)

                if output:
                    Path(output).write_text(formatted_output)
                    console.print(f"[green]✓[/green] Results saved to {output}")
                else:
                    # Print JSON to console using click.echo
                    click.echo(formatted_output)
            except Exception as e:
                console.print(f"[red]Error formatting JSON:[/red] {str(e)}")
                raise click.Abort() from e

        elif output_format == "csv":
            try:
                # Use the new CSV formatter from formatters module
                formatted_output = format_as_csv(issues)

                if output:
                    Path(output).write_text(formatted_output)
                    console.print(f"[green]✓[/green] Results saved to {output}")
                else:
                    # Print CSV to console using click.echo
                    click.echo(formatted_output)
            except Exception as e:
                console.print(f"[red]Error formatting CSV:[/red] {str(e)}")
                raise click.Abort() from e

        elif output_format == "jsonl":
            try:
                # Use the JSONL formatter from formatters module
                formatted_output = format_as_jsonl(issues)

                if output:
                    Path(output).write_text(formatted_output)
                    console.print(f"[green]✓[/green] Results saved to {output}")
                else:
                    # Print JSONL to console using click.echo
                    click.echo(formatted_output)
            except Exception as e:
                console.print(f"[red]Error formatting JSONL:[/red] {str(e)}")
                raise click.Abort() from e

        else:  # format == 'table' (default)
            format_issues_table(issues)
            console.print(f"\n[dim]Found {len(issues)} issue(s)[/dim]")

            if output:
                console.print(
                    "[yellow]Note: Table format cannot be saved to file. Use --format json, --format csv, or --format jsonl for file output.[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
def transitions(issue_key: str) -> None:
    """Show available transitions for an issue."""
    try:
        client = JiraClient()

        with console.status(f"Getting transitions for {issue_key}..."):
            transitions = client.get_transitions(issue_key)

        if transitions:
            console.print(f"\n[bold]Available transitions for {issue_key}:[/bold]")
            for t in transitions:
                console.print(f"  • {t['name']} (ID: {t['id']})")
        else:
            console.print("[yellow]No transitions available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
def types(project: str) -> None:
    """List available issue types for a project."""
    try:
        client = JiraClient()

        with console.status(f"Fetching issue types for {project}..."):
            issue_types = client.get_issue_types(project)

        if not issue_types:
            console.print(f"[yellow]No issue types found for project {project}[/yellow]")
            return

        from rich.table import Table

        from temet_jira.document.builders.profiles import TYPE_PROFILES

        table = Table(title=f"Issue Types — {project}")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Subtask", style="yellow")
        table.add_column("Custom Profile", style="green")

        for it in sorted(issue_types, key=lambda x: x.get("name", "")):
            name = it.get("name", "Unknown")
            subtask = "Yes" if it.get("subtask", False) else "No"
            has_profile = "Yes" if name.lower() in TYPE_PROFILES else "No"
            table.add_row(name, subtask, has_profile)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.option("--summary", "-s", required=True, help="Issue summary/title")
@click.option("--description", "-d", help="Issue description")
@click.option(
    "--type",
    "-t",
    "issue_type",
    default="Task",
    help="Issue type — run 'temet-jira types' to see available types",
)
@click.option("--epic", "-e", help="Epic key to link to (e.g., PROJ-123)")
@click.option("--priority", "-p", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
def create(
    summary: str,
    description: str | None,
    issue_type: str,
    epic: str | None,
    priority: str | None,
    labels: str | None,
    project: str,
) -> None:
    """Create a new issue in Jira with professional formatting."""
    try:
        client = JiraClient()

        # Parse labels if provided
        label_list = [label.strip() for label in labels.split(",")] if labels else None

        # Build ADF description using TypedBuilder
        # Pass only description — header fields are optional from CLI.
        # For richer documents, use the programmatic API or --description-adf.
        builder = TypedBuilder(issue_type, summary)
        if description:
            builder.add_section_optional("description", text=description)

        fields: dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": builder.build(),
        }

        # Add priority if provided
        if priority:
            fields["priority"] = {"name": priority}

        # Add labels if provided
        if label_list:
            fields["labels"] = label_list

        # Add epic link if provided and not an epic
        if epic and issue_type.lower() != "epic":
            fields["customfield_10014"] = epic  # Epic Link field

        with console.status(f"Creating {issue_type.lower()} in project {project}..."):
            result = client.create_issue(fields)

        issue_key = result.get("key")
        console.print(
            f"[green]\u2713[/green] {issue_type} created successfully: {issue_key}"
        )

        # Show the created issue
        if issue_key:
            issue = client.get_issue(issue_key)
            format_issue(issue)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
@click.option(
    "--max-results",
    "-n",
    default=None,
    type=int,
    help=f"Maximum number of epics to show (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()})",
)
def epics(project: str, max_results: int | None) -> None:
    """List all epics in a project."""
    try:
        client = JiraClient()

        with console.status(f"Fetching epics for project {project}..."):
            epics = client.get_epics(project, max_results)

        if epics:
            format_issues_table(epics)
            console.print(f"\n[dim]Found {len(epics)} epic(s) in {project}[/dim]")
        else:
            console.print(f"[yellow]No epics found in project {project}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("epic_key")
@click.option(
    "--show-children", "-c", is_flag=True, help="Show child issues of the epic"
)
def epic_details(epic_key: str, show_children: bool) -> None:
    """Get detailed information about an epic including child issues."""
    try:
        client = JiraClient()

        # Get the epic details
        with console.status(f"Fetching epic {epic_key}..."):
            epic = client.get_issue(epic_key)

        # Display epic details
        format_issue(epic)

        # If requested, show child issues
        if show_children:
            console.print("\n[bold]Child Issues:[/bold]")
            with console.status("Fetching child issues..."):
                # Try different queries for finding child issues
                # Method 1: Using parent field (for newer Jira)
                try:
                    children, _ = client.search_issues(
                        f"parent = {epic_key}", max_results=100
                    )
                except Exception:
                    # Method 2: Try with Epic Link custom field
                    try:
                        epic_link_field = client.get_epic_link_field()
                        if epic_link_field:
                            children, _ = client.search_issues(
                                f"{epic_link_field} = {epic_key}", max_results=100
                            )
                        else:
                            # Method 3: Try common Epic Link field name
                            children, _ = client.search_issues(
                                f'"Epic Link" = {epic_key}', max_results=100
                            )
                    except Exception:
                        console.print(
                            "[yellow]Unable to fetch child issues - epic link field may not be available[/yellow]"
                        )
                        children = []

            if children:
                format_issues_table(children)
                console.print(f"\n[dim]Found {len(children)} child issue(s)[/dim]")
            else:
                console.print("[yellow]No child issues found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.command(name="export")
@click.option(
    "--project",
    "-p",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key to export from. Configurable via JIRA_DEFAULT_PROJECT",
)
@click.option(
    "--status",
    help="Filter by status (e.g., 'Open', 'In Progress'). Default: Not in (Done, Closed, Cancelled)",
)
@click.option("--assignee", help="Filter by assignee name/email, 'unassigned', or 'me'")
@click.option("--priority", help="Filter by priority (e.g., 'High', 'Medium', 'Low')")
@click.option(
    "--type", "issue_type", help="Filter by issue type (e.g., 'Bug', 'Story', 'Task')"
)
@click.option(
    "--component",
    default=lambda: os.environ.get("JIRA_DEFAULT_COMPONENT"),
    help="Filter by component name (e.g., 'Backend'). Configurable via JIRA_DEFAULT_COMPONENT",
)
@click.option(
    "--created", help="Filter by creation date (e.g., '-7d', '>= 2024-01-01')"
)
@click.option("--jql", help="Custom JQL query (overrides other filters)")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "csv", "jsonl"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
@click.option(
    "--output", "-o", help="Output file path (required for json/csv/jsonl formats)"
)
@click.option("--stats", is_flag=True, help="Display summary statistics")
@click.option(
    "--group-by",
    type=click.Choice(["status", "assignee", "priority"], case_sensitive=False),
    help="Group results by specified field",
)
@click.option(
    "--expand",
    help="Fields to expand (e.g., 'changelog', 'transitions') - comma-separated",
)
@click.option(
    "--limit",
    "-n",
    default=None,
    type=int,
    help=f"Maximum number of results (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()})",
)
@click.option(
    "--all", "fetch_all", is_flag=True, help="Fetch all results (bypass limit)"
)
def export_cmd(
    project: str,
    status: str | None,
    assignee: str | None,
    priority: str | None,
    issue_type: str | None,
    component: str | None,
    created: str | None,
    jql: str | None,
    output_format: str,
    output: str | None,
    stats: bool,
    group_by: str | None,
    expand: str | None,
    limit: int | None,
    fetch_all: bool,
) -> None:
    """Export project issues with flexible filtering and formatting.

    Examples:

        # Export using default project from .env
        temet-jira export --format csv -o tickets.csv

        # Export specific project
        temet-jira export --project PROJ --format csv -o tickets.csv

        # Export all tickets to JSONL
        temet-jira export -p PROJ --all --format jsonl -o all_tickets.jsonl

        # Get high priority tickets with statistics
        temet-jira export --priority High --stats

        # Export filtered tickets grouped by assignee
        temet-jira export --status "In Progress" --group-by assignee

        # Use custom JQL query
        temet-jira export --jql "assignee = currentUser()" --format json -o my_tickets.json
    """
    try:
        client = JiraClient()

        # Use default limit if not specified
        if limit is None:
            limit = _get_default_max_results()

        # Build JQL query
        if jql:
            # Use custom JQL if provided
            jql_query = jql
        else:
            filters = [f"project = {project}"]

            # Add status filter
            if status:
                if status.lower() in ["open", "active", "all"]:
                    filters.append("status NOT IN (Done, Closed, Cancelled)")
                else:
                    filters.append(f'status = "{status}"')
            else:
                # Default: exclude closed statuses
                filters.append("status NOT IN (Done, Closed, Cancelled)")

            # Add assignee filter
            if assignee:
                if assignee.lower() == "unassigned":
                    filters.append("assignee = EMPTY")
                elif assignee.lower() == "me":
                    filters.append("assignee = currentUser()")
                else:
                    filters.append(f'assignee ~ "{assignee}"')

            # Add priority filter
            if priority:
                filters.append(f'priority = "{priority}"')

            # Add issue type filter
            if issue_type:
                filters.append(f'issuetype = "{issue_type}"')

            # Add component filter
            if component:
                filters.append(f'component = "{component}"')

            # Add created date filter
            if created:
                filters.append(f"created >= {created}")

            jql_query = " AND ".join(filters)

        console.print(f"[dim]Query: {jql_query}[/dim]\n")

        # Parse expand options
        expand_list = (
            [e.strip() for e in expand.split(",")]
            if expand and expand.strip()
            else None
        )

        # Define fields to fetch
        fields = [
            "key",
            "summary",
            "status",
            "assignee",
            "priority",
            "issuetype",
            "created",
            "updated",
            "description",
            "labels",
        ]

        # Fetch issues (with pagination if --all is specified)
        if fetch_all:
            with console.status("Fetching all issues..."):
                issues = client.search_all_issues(
                    jql_query, fields=fields, expand=expand_list, max_per_page=limit
                )
            console.print(f"[green]✓[/green] Fetched {len(issues)} issue(s) total\n")
        else:
            with console.status("Fetching issues..."):
                issues, is_last = client.search_issues(
                    jql_query, fields=fields, expand=expand_list, max_results=limit
                )

            # Warn if results are truncated (only for interactive/table output)
            if output_format == "table" or output:
                if not is_last:
                    console.print(
                        f"[yellow]⚠️  Retrieved {len(issues)} results (more available)[/yellow]"
                    )
                    console.print(
                        "[yellow]   To get all results: Add --all flag to this command[/yellow]\n"
                    )
                else:
                    console.print(f"[green]✓[/green] Fetched {len(issues)} issue(s)\n")

        if not issues:
            console.print("[yellow]No issues found matching the criteria.[/yellow]")
            return

        # Display statistics if requested
        if stats:
            by_status: defaultdict[str, int] = defaultdict(int)
            by_priority: defaultdict[str, int] = defaultdict(int)
            by_assignee: defaultdict[str, int] = defaultdict(int)
            by_type: defaultdict[str, int] = defaultdict(int)

            for issue in issues:
                fields_data = issue.get("fields", {})
                issue_status = fields_data.get("status", {}).get("name", "Unknown")
                issue_priority = fields_data.get("priority", {}).get("name", "Unknown")
                issue_issuetype = fields_data.get("issuetype", {}).get(
                    "name", "Unknown"
                )
                assignee_obj = fields_data.get("assignee")
                issue_assignee = (
                    assignee_obj.get("displayName", "Unassigned")
                    if assignee_obj
                    else "Unassigned"
                )

                by_status[issue_status] += 1
                by_priority[issue_priority] += 1
                by_assignee[issue_assignee] += 1
                by_type[issue_issuetype] += 1

            # Print summary
            console.print("[bold]SUMMARY STATISTICS[/bold]")
            console.print(f"Total Issues: {len(issues)}\n")

            console.print("[bold]By Status:[/bold]")
            for s, count in sorted(by_status.items()):
                console.print(f"  {s}: {count}")

            console.print("\n[bold]By Priority:[/bold]")
            for p, count in sorted(by_priority.items()):
                console.print(f"  {p}: {count}")

            console.print("\n[bold]By Type:[/bold]")
            for t, count in sorted(by_type.items()):
                console.print(f"  {t}: {count}")

            console.print("\n[bold]By Assignee:[/bold]")
            for a, count in sorted(by_assignee.items()):
                console.print(f"  {a}: {count}")

            console.print()

        # Display grouped results if requested
        if group_by:
            groups = defaultdict(list)

            for issue in issues:
                fields_data = issue.get("fields", {})

                if group_by == "status":
                    key = fields_data.get("status", {}).get("name", "Unknown")
                elif group_by == "assignee":
                    assignee_obj = fields_data.get("assignee")
                    key = (
                        assignee_obj.get("displayName", "Unassigned")
                        if assignee_obj
                        else "Unassigned"
                    )
                elif group_by == "priority":
                    key = fields_data.get("priority", {}).get("name", "Unknown")
                else:
                    key = "Unknown"

                groups[key].append(issue)

            console.print(f"[bold]GROUPED BY {group_by.upper()}[/bold]\n")

            for group_key in sorted(groups.keys()):
                items = groups[group_key]
                console.print(
                    f"[bold cyan]{group_key}[/bold cyan] ({len(items)} issues):"
                )

                for issue in items:
                    key = issue.get("key")
                    summary_text = issue.get("fields", {}).get("summary", "")[:70]
                    issue_status = (
                        issue.get("fields", {}).get("status", {}).get("name", "")
                    )
                    console.print(f"  {key:<12} {summary_text:<70} [{issue_status}]")

                console.print()

        # Handle output format
        if output_format == "json":
            if not output and not stats and not group_by:
                # Print to console
                formatted_output = format_as_json(issues, indent=2)
                click.echo(formatted_output)
            elif output:
                # Save to file
                formatted_output = format_as_json(issues, indent=2)
                Path(output).write_text(formatted_output)
                console.print(
                    f"[green]✓[/green] Exported {len(issues)} issues to {output}"
                )
            else:
                console.print(
                    "[yellow]Note: Use --output/-o to save JSON to file[/yellow]"
                )

        elif output_format == "csv":
            if not output:
                if not stats and not group_by:
                    # Print to console
                    formatted_output = format_as_csv(issues)
                    click.echo(formatted_output)
                else:
                    console.print(
                        "[yellow]Error: --output/-o is required for CSV format when using --stats or --group-by[/yellow]"
                    )
                    raise click.Abort()
            else:
                # Save to file
                formatted_output = format_as_csv(issues)
                Path(output).write_text(formatted_output)
                console.print(
                    f"[green]✓[/green] Exported {len(issues)} issues to {output}"
                )

        elif output_format == "jsonl":
            if not output and not stats and not group_by:
                # Print to console
                formatted_output = format_as_jsonl(issues)
                click.echo(formatted_output)
            elif output:
                # Save to file
                formatted_output = format_as_jsonl(issues)
                Path(output).write_text(formatted_output)
                console.print(
                    f"[green]✓[/green] Exported {len(issues)} issues to {output}"
                )
            else:
                console.print(
                    "[yellow]Note: Use --output/-o to save JSONL to file[/yellow]"
                )

        else:  # table format (default)
            if output:
                console.print(
                    "[yellow]Note: Table format cannot be saved to file. Use --format json, --format csv, or --format jsonl for file output.[/yellow]"
                )

            if not stats and not group_by:
                # Only show table if not already showing stats/groups
                format_issues_table(issues)
                console.print(f"\n[dim]Total: {len(issues)} issue(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e


@jira.group(name="analyze")
def analyze() -> None:
    """Analyze Jira issues and generate reports."""
    pass


@analyze.command(name="state-durations")
@click.argument(
    "input_file", type=click.Path(exists=True, readable=True, path_type=Path)
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(path_type=Path),
    help="Output CSV file path",
)
@click.option("--date-from", help="Start date filter (YYYY-MM-DD)")
@click.option("--date-to", help="End date filter (YYYY-MM-DD)")
@click.option("--business-hours", is_flag=True, help="Use business hours calculation")
@click.option(
    "--timezone", default="UTC", help="Timezone for calculations (default: UTC)"
)
def state_durations(
    input_file: Path,
    output: Path,
    date_from: str | None,
    date_to: str | None,
    business_hours: bool,
    timezone: str,
) -> None:
    """Analyze state durations for Jira issues from a JSON file.

    Reads a JSON file containing Jira issues and calculates the time spent in each state.
    Outputs the results to a CSV file.

    Example:
        temet-jira analyze state-durations issues.json -o durations.csv
    """
    try:
        # Read the JSON file
        with console.status(f"Reading issues from {input_file}..."):
            try:
                with open(input_file) as f:
                    issues_data = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON file: {e}")
                raise click.Abort() from e
            except FileNotFoundError:
                console.print(f"[red]Error:[/red] File not found: {input_file}")
                raise click.Abort() from None
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read file: {e}")
                raise click.Abort() from e

        # Validate it's a list of issues
        if not isinstance(issues_data, list):
            console.print(
                "[red]Error:[/red] Input file must contain a JSON array of issues"
            )
            raise click.Abort()

        if not issues_data:
            console.print("[yellow]Warning:[/yellow] No issues found in input file")
            # Create empty output file
            with open(output, "w", newline="") as f:
                empty_writer = csv.writer(f)
                empty_writer.writerow(
                    ["issue_key", "summary", "current_status", "created", "updated"]
                )
            console.print(f"[green]✓[/green] Empty results saved to {output}")
            return

        console.print(f"[dim]Found {len(issues_data)} issue(s) to analyze[/dim]")

        # Filter by date range if specified
        filtered_issues = issues_data
        if date_from or date_to:
            filtered_issues = []
            # Parse dates as timezone-aware (assume UTC if no timezone specified)
            date_from_obj = (
                datetime.fromisoformat(date_from + "T00:00:00+00:00")
                if date_from
                else None
            )
            date_to_obj = (
                datetime.fromisoformat(date_to + "T23:59:59+00:00") if date_to else None
            )

            for issue in issues_data:
                created_str = issue.get("fields", {}).get("created")
                if created_str:
                    try:
                        # Normalize various date formats from Jira
                        created_date = datetime.fromisoformat(
                            created_str.replace("Z", "+00:00")
                            .replace(".000+0000", "+00:00")
                            .replace(".000Z", "+00:00")
                        )
                        if date_from_obj and created_date < date_from_obj:
                            continue
                        if date_to_obj and created_date > date_to_obj:
                            continue
                        filtered_issues.append(issue)
                    except (ValueError, AttributeError):
                        # If we can't parse the date, include the issue
                        filtered_issues.append(issue)
                else:
                    filtered_issues.append(issue)

            console.print(
                f"[dim]After date filtering: {len(filtered_issues)} issue(s)[/dim]"
            )

        # Initialize the analyzer
        analyzer = StateDurationAnalyzer()

        # Process issues with progress indicator for large datasets
        if len(filtered_issues) > 50:
            console.print("[dim]Processing large dataset...[/dim]")
            with console.status("Analyzing state durations..."):
                try:
                    # Pass full issue data to analyzer, not just keys
                    # The analyzer might need the full issue data for proper analysis

                    # Call the appropriate analyzer method
                    if business_hours:
                        # Try business hours method if it exists
                        if hasattr(analyzer, "analyze_issues_business_hours"):
                            results = analyzer.analyze_issues_business_hours(
                                filtered_issues, timezone=timezone
                            )
                        else:
                            # Fall back to regular analysis
                            results = analyzer.analyze_issues(filtered_issues)
                            console.print(
                                "[yellow]Note:[/yellow] Business hours calculation not yet implemented"
                            )
                    else:
                        results = analyzer.analyze_issues(filtered_issues)
                except NotImplementedError:
                    # If analyzer methods are not implemented yet, create dummy results
                    console.print(
                        "[yellow]Note:[/yellow] State analysis not fully implemented, generating basic output"
                    )
                    results = []
                    for issue in filtered_issues:
                        results.append(
                            {
                                "issue_key": issue.get("key", ""),
                                "summary": issue.get("fields", {}).get("summary", ""),
                                "current_status": issue.get("fields", {})
                                .get("status", {})
                                .get("name", ""),
                                "created": issue.get("fields", {}).get("created", ""),
                                "updated": issue.get("fields", {}).get("updated", ""),
                                "state_durations": {},
                            }
                        )
        else:
            try:
                # Pass full issue data to analyzer, not just keys
                # The analyzer might need the full issue data for proper analysis

                # Call the appropriate analyzer method
                if business_hours:
                    # Try business hours method if it exists
                    if hasattr(analyzer, "analyze_issues_business_hours"):
                        results = analyzer.analyze_issues_business_hours(
                            filtered_issues, timezone=timezone
                        )
                    else:
                        # Fall back to regular analysis
                        results = analyzer.analyze_issues(filtered_issues)
                        console.print(
                            "[yellow]Note:[/yellow] Business hours calculation not yet implemented"
                        )
                else:
                    results = analyzer.analyze_issues(filtered_issues)
            except NotImplementedError:
                # If analyzer methods are not implemented yet, create dummy results
                console.print(
                    "[yellow]Note:[/yellow] State analysis not fully implemented, generating basic output"
                )
                results = []
                for issue in filtered_issues:
                    results.append(
                        {
                            "issue_key": issue.get("key", ""),
                            "summary": issue.get("fields", {}).get("summary", ""),
                            "current_status": issue.get("fields", {})
                            .get("status", {})
                            .get("name", ""),
                            "created": issue.get("fields", {}).get("created", ""),
                            "updated": issue.get("fields", {}).get("updated", ""),
                            "state_durations": {},
                        }
                    )

        # Write results to CSV using the analyzer's format_as_csv method if available
        with console.status(f"Writing results to {output}..."):
            # Check if we have the new format with durations
            if results and "durations" in results[0]:
                # Use the new format_as_csv method
                csv_output = analyzer.format_as_csv(
                    results, include_business_hours=business_hours
                )
                output.write_text(csv_output)
            else:
                # Fall back to the old format for backward compatibility
                with open(output, "w", newline="") as csvfile:
                    # Basic fields
                    fieldnames: list[str] = [
                        "issue_key",
                        "summary",
                        "current_status",
                        "created",
                        "updated",
                    ]

                    # Add state duration columns if available
                    if results:
                        all_states: set[str] = set()
                        for result in results:
                            if "state_durations" in result and isinstance(
                                result["state_durations"], dict
                            ):
                                all_states.update(result["state_durations"].keys())

                        # Sort states for consistent column order
                        for state in sorted(all_states):
                            fieldnames.append(f"duration_{state}")

                    dict_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    dict_writer.writeheader()

                    # Write rows
                    for result in results:
                        row: dict[str, Any] = {
                            "issue_key": result.get("issue_key", ""),
                            "summary": result.get("summary", ""),
                            "current_status": result.get("current_status", ""),
                            "created": result.get("created", ""),
                            "updated": result.get("updated", ""),
                        }

                        # Add state durations
                        if "state_durations" in result and isinstance(
                            result["state_durations"], dict
                        ):
                            for state, duration in result["state_durations"].items():
                                row[f"duration_{state}"] = duration

                        dict_writer.writerow(row)

        console.print(f"[green]✓[/green] Successfully analyzed {len(results)} issue(s)")
        console.print(f"[green]✓[/green] Results saved to {output}")

    except click.Abort:
        # Already handled, just re-raise
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] Unexpected error: {e}")
        raise click.Abort() from e


# =============================================================================
# Configuration Commands
# =============================================================================


@jira.command()
def setup() -> None:
    """Interactive setup wizard for temet-jira configuration.

    Guides you through configuring your Jira credentials and saves them
    to ~/.config/temet-jira/config.yaml for future use.
    """
    from rich.panel import Panel

    console.print()
    console.print(
        Panel.fit(
            "[bold blue]temet-jira Setup Wizard[/bold blue]\n\n"
            "This will help you configure temet-jira with your Jira credentials.\n"
            f"Configuration will be saved to: [cyan]{get_config_path()}[/cyan]",
            border_style="blue",
        )
    )
    console.print()

    # Check if already configured
    if is_configured():
        console.print("[yellow]⚠️  temet-jira is already configured.[/yellow]")
        console.print()
        existing = get_all_config()
        console.print("[dim]Current configuration:[/dim]")
        for key, info in existing.items():
            if info["value"]:
                console.print(f"  {key}: {mask_sensitive(info['value'], key)} ({info['source']})")
        console.print()

        if Prompt.ask("Do you want to reconfigure?", choices=["y", "n"], default="n") != "y":
            console.print("[dim]Setup cancelled.[/dim]")
            return

    console.print()
    console.print("[bold]Step 1: Jira Instance URL[/bold]")
    console.print("[dim]This is your Jira Cloud URL (e.g., https://company.atlassian.net)[/dim]")

    current_url = get_value("base_url")
    base_url = Prompt.ask(
        "Jira URL",
        default=current_url or "https://your-company.atlassian.net",
    )

    # Validate URL format
    if not base_url.startswith("https://"):
        console.print("[yellow]Warning: URL should start with https://[/yellow]")
        if not base_url.startswith("http"):
            base_url = "https://" + base_url

    # Remove trailing slash
    base_url = base_url.rstrip("/")

    console.print()
    console.print("[bold]Step 2: Your Email Address[/bold]")
    console.print("[dim]The email you use to log into Jira[/dim]")

    current_username = get_value("username")
    username = Prompt.ask(
        "Email",
        default=current_username or "",
    )

    console.print()
    console.print("[bold]Step 3: API Token[/bold]")
    console.print("[dim]Generate at: https://id.atlassian.com/manage-profile/security/api-tokens[/dim]")
    console.print("[dim]The token will be stored securely and masked in displays.[/dim]")

    api_token = Prompt.ask(
        "API Token",
        password=True,
    )

    if not api_token:
        console.print("[red]Error: API token is required[/red]")
        raise click.Abort()

    console.print()
    console.print("[bold]Step 4: Project (Optional)[/bold]")
    console.print("[dim]Set a project key to avoid typing --project every time[/dim]")

    current_project = get_value("project")
    project = Prompt.ask(
        "Project key",
        default=current_project or "",
    )

    # Save configuration
    console.print()
    console.print("[dim]Saving configuration...[/dim]")

    try:
        set_value("base_url", base_url)
        set_value("username", username)
        set_value("api_token", api_token)
        if project:
            set_value("project", project)

        console.print(f"[green]✓[/green] Configuration saved to {get_config_path()}")
    except Exception as e:
        console.print(f"[red]Error saving configuration:[/red] {e}")
        raise click.Abort() from e

    # Test the connection
    console.print()
    console.print("[dim]Testing connection...[/dim]")

    try:
        client = JiraClient(
            base_url=base_url,
            username=username,
            api_token=api_token,
        )
        # Try to get current user info
        response = client.session.get(f"{base_url}/rest/api/3/myself")
        if response.status_code == 200:
            user_data = response.json()
            display_name = user_data.get("displayName", username)
            console.print(f"[green]✓[/green] Connected successfully as [bold]{display_name}[/bold]")
        else:
            console.print(f"[yellow]⚠️  Connection test returned status {response.status_code}[/yellow]")
            console.print("[dim]Configuration saved, but you may need to verify your credentials.[/dim]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Connection test failed:[/yellow] {e}")
        console.print("[dim]Configuration saved, but please verify your credentials.[/dim]")

    console.print()
    console.print("[bold green]Setup complete![/bold green]")
    console.print()
    console.print("Try these commands:")
    console.print("  [cyan]temet-jira config[/cyan]        - View your configuration")
    if project:
        console.print(f"  [cyan]temet-jira export[/cyan]        - Export tickets from {project}")
    console.print("  [cyan]temet-jira search \"status = Open\"[/cyan]  - Search for issues")
    console.print()


@jira.group(name="config")
def config_cmd() -> None:
    """View and manage temet-jira configuration."""
    pass


@config_cmd.command(name="show")
def config_show() -> None:
    """Show current configuration."""
    from rich.table import Table

    config = get_all_config()

    if not any(info["value"] for info in config.values()):
        console.print("[yellow]No configuration found.[/yellow]")
        console.print(f"[dim]Config file location: {get_config_path()}[/dim]")
        console.print()
        console.print("Run [cyan]temet-jira setup[/cyan] to configure.")
        return

    table = Table(title="temet-jira Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_column("Source", style="dim")

    for key, info in config.items():
        value = mask_sensitive(info["value"], key)
        table.add_row(key, value, info["source"])

    console.print(table)
    console.print()
    console.print(f"[dim]Config file: {get_config_path()}[/dim]")


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    Example:
        temet-jira config set project PROJ
    """
    try:
        set_value(key, value)
        display_value = mask_sensitive(value, key)
        console.print(f"[green]✓[/green] Set {key} = {display_value}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print()
        console.print("[dim]Valid keys:[/dim]")
        for k, desc in VALID_KEYS.items():
            console.print(f"  [cyan]{k}[/cyan] - {desc}")
        raise click.Abort() from e


@config_cmd.command(name="get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value.

    Example:
        temet-jira config get base_url
    """
    value = get_value(key)
    if value:
        display_value = mask_sensitive(value, key)
        console.print(display_value)
    else:
        console.print(f"[yellow]{key} is not set[/yellow]")
        raise click.Abort()


@config_cmd.command(name="unset")
@click.argument("key")
def config_unset(key: str) -> None:
    """Remove a configuration value.

    Example:
        temet-jira config unset project
    """
    if delete_value(key):
        console.print(f"[green]✓[/green] Removed {key}")
    else:
        console.print(f"[yellow]{key} was not set in config file[/yellow]")


@config_cmd.command(name="path")
def config_path() -> None:
    """Show the config file path."""
    path = get_config_path()
    console.print(str(path))
    if config_exists():
        console.print("[dim](file exists)[/dim]")
    else:
        console.print("[dim](file does not exist)[/dim]")


@config_cmd.command(name="edit")
def config_edit() -> None:
    """Open config file in default editor."""
    import subprocess

    path = get_config_path()

    if not config_exists():
        console.print("[yellow]Config file does not exist yet.[/yellow]")
        console.print("Run [cyan]temet-jira setup[/cyan] first, or create it manually.")
        return

    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(path)], check=True)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Editor '{editor}' not found")
        console.print(f"[dim]Set EDITOR environment variable or edit manually: {path}[/dim]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Editor exited with error: {e}")


# Make 'temet-jira config' with no subcommand show the config
@config_cmd.result_callback()
@click.pass_context
def config_default(ctx: click.Context, *args: Any, **kwargs: Any) -> None:
    """Show config if no subcommand is given."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(config_show)


# ---------------------------------------------------------------------------
# MCP commands
# ---------------------------------------------------------------------------

# Each entry: (display name, config file path, json_key, snippet_format)
# snippet_format: "standard" | "vscode" | "zed"
_MCP_TARGETS: list[tuple[str, str | None, str, str]] = [
    ("Claude Code — global (~/.claude.json)", "~/.claude.json", "mcpServers", "standard"),
    ("Claude Code — project (.claude/settings.json)", ".claude/settings.json", "mcpServers", "standard"),
    ("Cursor — global (~/.cursor/mcp.json)", "~/.cursor/mcp.json", "mcpServers", "standard"),
    ("Cursor — project (.cursor/mcp.json)", ".cursor/mcp.json", "mcpServers", "standard"),
    ("Windsurf (~/.codeium/windsurf/mcp_config.json)", "~/.codeium/windsurf/mcp_config.json", "mcpServers", "standard"),
    ("VS Code / Copilot — project (.vscode/mcp.json)", ".vscode/mcp.json", "servers", "vscode"),
    ("Zed (~/.config/zed/settings.json)", "~/.config/zed/settings.json", "context_servers", "zed"),
    ("Other — show generic snippet", None, "mcpServers", "standard"),
]


def _build_snippet(json_key: str, fmt: str, include_env: bool) -> str:
    env_block = ""
    if include_env:
        env_block = (
            ',\n      "env": {\n'
            '        "JIRA_BASE_URL": "https://your-company.atlassian.net",\n'
            '        "JIRA_USERNAME": "your-email@example.com",\n'
            '        "JIRA_API_TOKEN": "your-api-token"\n'
            "      }"
        )

    if fmt == "vscode":
        inner = (
            f'"temet-jira": {{\n'
            f'      "type": "stdio",\n'
            f'      "command": "temet-jira-mcp"'
            f"{env_block}\n    }}"
        )
    elif fmt == "zed":
        inner = (
            '"temet-jira": {\n'
            '      "command": {\n'
            '        "path": "temet-jira-mcp",\n'
            '        "args": []\n'
            "      }\n    }"
        )
    else:
        inner = (
            f'"temet-jira": {{\n'
            f'      "command": "temet-jira-mcp"'
            f"{env_block}\n    }}"
        )

    return f'"{json_key}": {{\n    {inner}\n  }}'


@jira.group(name="mcp")
def mcp_cmd() -> None:
    """Manage MCP server configuration."""


@mcp_cmd.command(name="add")
def mcp_add() -> None:
    """Print the MCP config snippet for your IDE or AI client.

    Scans common config file locations and guides you to the right snippet.
    """

    console.print("\n[bold]temet-jira MCP setup[/bold]\n")

    # Detect which config files already exist
    detected: list[int] = []
    for i, (_label, path_str, _, _) in enumerate(_MCP_TARGETS[:-1]):
        if path_str and Path(path_str).expanduser().exists():
            detected.append(i)

    if detected:
        console.print("[green]Detected existing config files:[/green]")
        for i in detected:
            label, path_str, _, _ = _MCP_TARGETS[i]
            console.print(f"  [cyan]{i + 1}.[/cyan] {label}")
        console.print()

    # Build choice list
    console.print("[bold]Where do you want to install the MCP server?[/bold]")
    for i, (label, _path_str, _, _) in enumerate(_MCP_TARGETS):
        exists_marker = " [green](file exists)[/green]" if i in detected else ""
        console.print(f"  [cyan]{i + 1}.[/cyan] {label}{exists_marker}")

    console.print()
    raw = Prompt.ask(
        "Enter number",
        default=str(detected[0] + 1) if detected else "1",
    )

    try:
        choice = int(raw.strip()) - 1
        if not 0 <= choice < len(_MCP_TARGETS):
            raise ValueError
    except ValueError:
        console.print("[red]Invalid choice.[/red]")
        raise SystemExit(1) from None

    label, path_str, json_key, fmt = _MCP_TARGETS[choice]

    # Check if env vars are already set
    has_env = all(
        os.environ.get(k)
        for k in ("JIRA_BASE_URL", "JIRA_USERNAME", "JIRA_API_TOKEN")
    )
    if has_env:
        console.print(
            "\n[green]✓[/green] JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN are already set "
            "in your environment — the [bold]env[/bold] block is optional.\n"
        )
        include_env_choice = Prompt.ask(
            "Include env block in snippet anyway?", choices=["y", "n"], default="n"
        )
        include_env = include_env_choice == "y"
    else:
        include_env = True

    snippet = _build_snippet(json_key, fmt, include_env)

    # Show target file
    if path_str:
        target = Path(path_str).expanduser()
        exists = target.exists()
        console.print(f"\n[bold]Target file:[/bold] {target}")
        if exists:
            console.print(
                f"[yellow]↳ File exists — merge the snippet into the "
                f'existing [cyan]"{json_key}"[/cyan] object.[/yellow]'
            )
        else:
            console.print(
                "[yellow]↳ File does not exist — create it with the content below.[/yellow]"
            )

    console.print("\n[bold]Add this to your config:[/bold]\n")

    if path_str and not Path(path_str).expanduser().exists():
        # Show full file for non-existent files
        full = "{\n  " + snippet + "\n}"
        console.print(f"[dim]# {Path(path_str).expanduser()}[/dim]")
        console.print(full)
    else:
        # Show merge snippet only
        console.print("[dim]# merge into your existing JSON:[/dim]")
        console.print("{")
        console.print("  // ... your existing config ...")
        console.print("  " + snippet.replace("\n", "\n  "))
        console.print("}")

    console.print(
        "\n[dim]Run [bold]temet-jira mcp tools[/bold] to see the list of available MCP tools.[/dim]\n"
    )


@mcp_cmd.command(name="tools")
def mcp_tools() -> None:
    """List all tools exposed by the temet-jira MCP server."""
    from rich.table import Table

    table = Table(title="temet-jira MCP Tools", show_header=True, header_style="bold cyan")
    table.add_column("Tool", style="bold")
    table.add_column("Description")

    tools = [
        ("get_issue", "Fetch a single issue by key (supports expand: transitions, changelog)"),
        ("search_issues", "Search with JQL — returns paginated issue list"),
        ("create_issue", "Create a new issue with summary, type, description, labels, priority"),
        ("update_issue", "Update fields or transition status"),
        ("add_comment", "Add a comment to an issue"),
        ("get_transitions", "List available status transitions for an issue"),
        ("transition_issue", "Move an issue to a new status"),
        ("get_epics", "List epics in a project"),
        ("get_issue_types", "List available issue types for a project"),
    ]
    for name, desc in tools:
        table.add_row(name, desc)

    console.print(table)
