"""Jira CLI commands."""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .analysis.formatters import format_as_csv, format_as_json, format_as_jsonl
from .analysis.state_analyzer import StateDurationAnalyzer
from .client import JiraClient
from .config import (
    VALID_KEYS,
    config_exists,
    delete_value,
    get_all_config,
    get_config_path,
    get_default_format,
    get_value,
    is_configured,
    load_project_meta,
    mask_sensitive,
    normalize_env_ref,
    save_project_meta,
    set_value,
)
from .document import DocumentBuilder, TypedBuilder
from .formatter import format_issue, format_issues_table
from .ui import console, err_console, is_interactive, SUCCESS, FAILURE, WARNING, INFO, BULLET, CHILD, format_status
from .ui.prompts import select, select_optional, checkbox, confirm, text as prompt_text

# Load environment variables from .env file
load_dotenv()


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
    "Configuration": ["setup", "config", "mcp"],
    "Reading": ["activity", "get", "search", "types"],
    "Epics": ["epics", "epic-details"],
    "Creating & Editing": ["create", "update", "comment", "transitions"],
    "Data & Analysis": ["export", "analyze"],
}

_CMD_TO_SECTION: dict[str, str] = {
    cmd: section for section, cmds in _SECTIONS.items() for cmd in cmds
}


class _HelpAwareCommand(click.Command):
    """click.Command that treats a trailing 'help' argument as --help."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and args[-1] == "help":
            args = ["--help"]
        return super().parse_args(ctx, args)


class _HelpAwareGroup(click.Group):
    """click.Group that treats 'help' as an alias for --help at every level."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and args[0] == "help":
            # "config help" → "config --help"
            args = ["--help"] + args[1:]
        elif len(args) == 2 and args[1] == "help":
            # "config set help" → "config set --help"  (immediate only — child groups handle deeper)
            args = [args[0], "--help"]
        return super().parse_args(ctx, args)

    def command(self, *args: object, **kwargs: object) -> object:
        kwargs.setdefault("cls", _HelpAwareCommand)
        return super().command(*args, **kwargs)  # type: ignore[misc]


class _SectionedGroup(_HelpAwareGroup):
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
    """Jira CLI — search, export, and manage issues via the Jira REST API v3.

    \b
    Run `temet-jira setup` to configure credentials before first use.
    Credentials: JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN (env or config file).

    \b
    Quick start:
        temet-jira setup            Configure your credentials
        temet-jira activity         View your active work
        temet-jira search "project = PROJ AND assignee = currentUser()"
        temet-jira export --format csv -o tickets.csv
    """
    pass


@jira.command()
@click.option("--project", "-p", help="Project key (overrides config default). Defaults to JIRA_DEFAULT_PROJECT env var or config.")
@click.option("--stale-days", default=3, show_default=True, help="Flag In-Progress issues with no update in this many days as stale.")
def activity(project: str | None, stale_days: int) -> None:
    """Show current sprint, backlog, and your active work.

    \b
    Displays three panels:
      - Project board(s) and active sprint
      - Your In-Progress and To-Do issues
      - Stale and Blocked issues

    \b
    Examples:
        temet-jira activity
        temet-jira activity --project PROJ
        temet-jira activity --stale-days 5
    """
    from datetime import timedelta, timezone

    client = JiraClient()
    project_key = project or get_value("project")

    with err_console.status("Fetching activity..."):
        myself = client.get_myself()
        account_id = myself.get("accountId", "")
        display_name = myself.get("displayName", "me")

        # --- Project / Sprint section ---
        boards = client.get_boards(project_key)
        board = boards[0] if boards else None

        active_sprint: dict[str, Any] | None = None
        backlog_count = 0

        if board:
            board_id = board["id"]
            try:
                active_sprint = client.get_active_sprint(board_id)
            except Exception:
                pass
            try:
                backlog_count = client.get_backlog_count(board_id)
            except Exception:
                pass

    def _board_url(board: dict[str, Any]) -> str:
        board_id = board["id"]
        proj = (board.get("location") or {}).get("projectKey", "")
        base = client.server_url
        if proj:
            return f"{base}/jira/software/projects/{proj}/boards/{board_id}"
        return f"{base}/secure/RapidBoard.jspa?rapidView={board_id}"

    project_table = Table.grid(padding=(0, 2))
    project_table.add_column(style="key", min_width=16)
    project_table.add_column()

    if boards:
        show = boards[:5]
        remainder = len(boards) - len(show)
        board_text = Text()
        for i, b in enumerate(show):
            name = b.get("name", str(b["id"]))
            url = _board_url(b)
            if i > 0:
                board_text.append("\n")
            board_text.append(name, style=f"link {url}")
            board_text.append(f"  {url}", style="muted")
        if remainder:
            board_text.append(f"\n(+{remainder} more)", style="muted")
        project_table.add_row("Boards", board_text)
    else:
        project_table.add_row("Boards", "[muted]none found[/muted]")

    if active_sprint:
        sprint_name = active_sprint.get("name", "Unknown")
        end_date_str = active_sprint.get("endDate", "")
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                days_left = (end_date - datetime.now(timezone.utc)).days
                sprint_label = f"[accent]{sprint_name}[/accent]  [muted]({days_left}d remaining)[/muted]"
            except ValueError:
                sprint_label = f"[accent]{sprint_name}[/accent]"
        else:
            sprint_label = f"[accent]{sprint_name}[/accent]"
        project_table.add_row("Current Sprint", sprint_label)
    else:
        project_table.add_row("Current Sprint", "[muted]no active sprint[/muted]")

    project_table.add_row("Backlog", str(backlog_count) if board else "[muted]—[/muted]")

    project_title = f"Project: {project_key}" if project_key else "Project"
    console.print(Panel(project_table, title=project_title, title_align="left", border_style="cyan"))

    # --- My Work section ---
    stale_cutoff = (datetime.now(timezone.utc) - timedelta(days=stale_days)).strftime("%Y-%m-%d")

    sprint_clause = f'sprint = "{active_sprint["name"]}"' if active_sprint else ""

    def _search(jql: str) -> list[dict[str, Any]]:
        try:
            issues, _ = client.search_issues(jql, fields=["summary", "status", "updated", "priority"], max_results=20)
            return issues
        except Exception:
            return []

    base = f'assignee = "{account_id}"' if account_id else "assignee = currentUser()"

    in_progress_jql = f'{base} AND status = "In Progress" AND resolution = Unresolved ORDER BY updated DESC'
    todo_jql_parts = [base, 'status = "To Do"', "resolution = Unresolved"]
    if sprint_clause:
        todo_jql_parts.append(sprint_clause)
    todo_jql = " AND ".join(todo_jql_parts) + " ORDER BY updated DESC"

    stale_jql = (
        f'{base} AND status = "In Progress" AND resolution = Unresolved '
        f'AND updated < "{stale_cutoff}" ORDER BY updated ASC'
    )
    blocked_jql = (
        f'{base} AND status in ("Blocked", "Impediment") AND resolution = Unresolved ORDER BY updated DESC'
    )

    in_progress = _search(in_progress_jql)
    todo = _search(todo_jql)
    stale = _search(stale_jql)
    blocked = _search(blocked_jql)

    work_table = Table.grid(padding=(0, 2))
    work_table.add_column(style="bold", min_width=18)
    work_table.add_column()

    def _fmt_issues(issues: list[dict[str, Any]], style: str = "") -> Text:
        if not issues:
            return Text("—", style="dim")
        lines = Text()
        for i, issue in enumerate(issues):
            key = issue.get("key", "")
            summary = (issue.get("fields") or {}).get("summary", "")
            if i > 0:
                lines.append("\n")
            lines.append(key, style="key")
            lines.append(f"  {summary}", style=style)
        return lines

    work_table.add_row("In Progress", _fmt_issues(in_progress))
    work_table.add_row("To Do", _fmt_issues(todo))

    stale_label = f"Stale (>{stale_days}d)"
    work_table.add_row(stale_label, _fmt_issues(stale, style="warning"))
    work_table.add_row("Blocked", _fmt_issues(blocked, style="error"))

    console.print(
        Panel(
            work_table,
            title=f"My Work  [muted]({display_name})[/muted]",
            title_align="left",
            border_style="green",
        )
    )


@jira.command()
@click.argument("issue_key")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default=get_default_format(),
    help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet.",
)
@click.option("--output", "-o", help="Output file path (optional; required for json/csv/jsonl to save to disk).")
@click.option(
    "--expand",
    help="Comma-separated fields to expand, e.g. changelog,transitions.",
)
@click.option(
    "--comments",
    is_flag=True,
    default=False,
    help="Fetch and display comments for the issue.",
)
@click.option(
    "--fields",
    type=click.Choice(["standard", "all"], case_sensitive=False),
    default="standard",
    help="Field set to display: standard (default) or all (includes Other Fields).",
)
@click.option("--web", is_flag=True, default=False, help="Open the issue in your browser instead of displaying it.")
def get(
    issue_key: str,
    output_format: str,
    output: str | None,
    expand: str | None,
    comments: bool,
    fields: str,
    web: bool,
) -> None:
    """Get details of a Jira issue.

    \b
    Priority: CLI flag > config file > env var > default

    \b
    Examples:
        temet-jira get PROJ-123
        temet-jira get PROJ-123 --comments
        temet-jira get PROJ-123 --format json
        temet-jira get PROJ-123 --format json -o issue.json
        temet-jira get PROJ-123 --expand changelog,transitions
        temet-jira get PROJ-123 --web
    """
    try:
        client = JiraClient()

        if web:
            import webbrowser
            webbrowser.open(f"{client.server_url}/browse/{issue_key}")
            return

        # Parse expand options — always include "names" for human-readable field labels
        expand_list = (
            [e.strip() for e in expand.split(",")]
            if expand and expand.strip()
            else []
        )
        if "names" not in expand_list:
            expand_list.append("names")

        with err_console.status(f"Fetching issue {issue_key}..."):
            issue = client.get_issue(issue_key, expand=expand_list)

        # Fetch comments if requested
        comment_list: list[dict[str, Any]] | None = None
        if comments:
            with err_console.status(f"Fetching comments for {issue_key}..."):
                comment_list = client.get_comments(issue_key)

        # Handle output format
        if output_format == "json":
            formatted = format_as_json([issue])
            if output:
                Path(output).write_text(formatted)
                console.print(f"[success]{SUCCESS}[/success] Issue saved to {output}")
            else:
                click.echo(formatted)
        elif output_format == "jsonl":
            formatted = format_as_jsonl([issue])
            if output:
                Path(output).write_text(formatted)
                console.print(f"[success]{SUCCESS}[/success] Issue saved to {output}")
            else:
                click.echo(formatted)
        elif output_format == "csv":
            formatted = format_as_csv([issue])
            if output:
                Path(output).write_text(formatted)
                console.print(f"[success]{SUCCESS}[/success] Issue saved to {output}")
            else:
                click.echo(formatted)
        else:  # table (default)
            if is_interactive():
                with console.pager(styles=True):
                    format_issue(issue, comments=comment_list, show_all_fields=(fields == "all"))
            else:
                format_issue(issue, comments=comment_list, show_all_fields=(fields == "all"))
            if output:
                console.print(
                    f"[warning]{WARNING}[/warning] Table format cannot be saved to file. "
                    "Use --format json or --format jsonl for file output."
                )

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
@click.option("--summary", help="Update issue summary.")
@click.option(
    "--description", help="Update issue description (plain text, converted to ADF automatically)."
)
@click.option(
    "--description-adf",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to a JSON file containing a valid ADF document for the description.",
)
@click.option("--assignee", help="Update assignee (account ID or email address).")
@click.option(
    "--priority", help="Update priority (Highest, High, Medium, Low, Lowest)."
)
@click.option("--labels", help="Update labels (comma-separated).")
@click.option("--status", help="Transition to a status by name (e.g. 'In Progress', 'Done'). Use `temet-jira transitions PROJ-123` to see valid names.")
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
    """Update fields or transition status on a Jira issue.

    --status accepts transition names (not IDs). Run `temet-jira transitions PROJ-123`
    to see which transitions are available for an issue.

    For rich description content (tables, panels, code blocks), create an ADF JSON
    file and pass it via --description-adf. ADF spec:
    https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

    \b
    Examples:
        temet-jira update PROJ-123 --status "In Progress"
        temet-jira update PROJ-123 --summary "New title" --priority High
        temet-jira update PROJ-123 --assignee user@example.com
        temet-jira update PROJ-123 --labels "bug,urgent"
        temet-jira update PROJ-123 --description-adf rich_desc.json
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
                        f"[error]{FAILURE}[/error] Invalid ADF format. Must be a JSON object with 'type': 'doc'"
                    )
                    raise click.Abort()
                fields["description"] = adf_content
            except json.JSONDecodeError as e:
                console.print(f"[error]{FAILURE}[/error] Invalid JSON in ADF file: {e}")
                raise click.Abort() from e
        elif description:
            # Use DocumentBuilder for proper ADF format
            builder = DocumentBuilder()
            builder.paragraph(description)
            fields["description"] = builder.build()

        if assignee:
            if "@" in assignee:
                console.print(
                    f"[warning]{WARNING}[/warning] Assignee should be an account ID, not email. Attempting anyway..."
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
            with err_console.status(f"Updating issue {issue_key}..."):
                client.update_issue(issue_key, fields)
            console.print(f"[success]{SUCCESS}[/success] Issue [key]{issue_key}[/key] updated successfully")

        # Handle status transition separately
        if status:
            with err_console.status("Getting available transitions..."):
                transitions = client.get_transitions(issue_key)

            # Find matching transition
            transition = None
            for t in transitions:
                if t["name"].lower() == status.lower():
                    transition = t
                    break

            if transition:
                with err_console.status(f"Transitioning to {status}..."):
                    client.transition_issue(issue_key, transition["id"])
                console.print(f"[success]{SUCCESS}[/success] Status changed to {format_status(status)}")
            else:
                available = ", ".join([format_status(t["name"]) for t in transitions])
                console.print(
                    f"[warning]{WARNING}[/warning] Status '{status}' not available. Available transitions: {available}"
                )

        # Show updated issue
        if fields or status:
            console.print("\n[header]Updated issue:[/header]")
            issue = client.get_issue(issue_key)
            format_issue(issue)
        else:
            console.print(f"[warning]{WARNING}[/warning] No updates specified")

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
@click.option("--message", "-m", help="Comment text (will prompt interactively if omitted).")
@click.option(
    "--adf",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to a JSON file containing a valid ADF document for rich comment formatting.",
)
def comment(issue_key: str, message: str | None, adf: Path | None) -> None:
    """Add a comment to a Jira issue.

    Use --message for plain text; use --adf for rich formatting (tables, panels,
    code blocks). --message and --adf are mutually exclusive.

    ADF spec: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

    \b
    Examples:
        temet-jira comment PROJ-123 --message "Fixed in v2.3"
        temet-jira comment PROJ-123 -m "Blocked by PROJ-456"
        temet-jira comment PROJ-123 --adf rich_comment.json
    """
    try:
        client = JiraClient()

        # Validate mutually exclusive options
        if message and adf:
            console.print(f"[error]{FAILURE}[/error] Cannot use both --message and --adf")
            raise click.Abort()

        if adf:
            # Load raw ADF from JSON file
            try:
                adf_body = json.loads(adf.read_text())
                # Validate basic ADF structure
                if not isinstance(adf_body, dict) or adf_body.get("type") != "doc":
                    console.print(
                        f"[error]{FAILURE}[/error] Invalid ADF format. Must be a JSON object with 'type': 'doc'"
                    )
                    raise click.Abort()
            except json.JSONDecodeError as e:
                console.print(f"[error]{FAILURE}[/error] Invalid JSON in ADF file: {e}")
                raise click.Abort() from e
        else:
            # Get comment text
            if not message:
                message = prompt_text("Comment")
                if not message:
                    console.print(f"[warning]{WARNING}[/warning] No comment provided")
                    return

            # Convert plain text to proper ADF format
            builder = DocumentBuilder()
            builder.paragraph(message)
            adf_body = builder.build()

        with err_console.status(f"Adding comment to {issue_key}..."):
            result = client.add_comment(issue_key, adf_body)

        console.print(f"[success]{SUCCESS}[/success] Comment added successfully")
        console.print(f"Comment ID: {result['id']}")

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("jql")
@click.option(
    "--max-results",
    "-n",
    default=None,
    type=int,
    help=f"Maximum number of results (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()}).",
)
@click.option("--fields", help="Specific fields to return (comma-separated).")
@click.option(
    "--expand", help="Comma-separated fields to expand, e.g. changelog,transitions."
)
@click.option("--output", "-o", help="Output file path (optional).")
@click.option("--columns", help="Table columns to display, comma-separated. Available: key,type,summary,status,priority,assignee,updated,created")
@click.option("--no-truncate", is_flag=True, default=False, help="Do not truncate long values in table output.")
@click.option("--no-headers", is_flag=True, default=False, help="Omit table headers (useful for scripting).")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default=get_default_format(),
    help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet.",
)
@click.option(
    "--all", "fetch_all", is_flag=True, help="Fetch all results, bypassing the limit (may be slow for large projects)."
)
def search(
    jql: str,
    max_results: int,
    fields: str | None,
    expand: str | None,
    output: str | None,
    output_format: str,
    fetch_all: bool,
    columns: str | None,
    no_truncate: bool,
    no_headers: bool,
) -> None:
    """Search for Jira issues using JQL.

    JQL reference: https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jql-queries/

    \b
    Priority: CLI flag > config file > env var > default

    \b
    Examples:
        temet-jira search "project = PROJ AND status = 'In Progress'"
        temet-jira search "assignee = currentUser() AND resolution = Unresolved"
        temet-jira search "project = PROJ AND priority = High" --format csv -o high_prio.csv
        temet-jira search "project = PROJ" --columns key,type,summary,status,assignee,updated,priority
        temet-jira search "project = PROJ" --all --format jsonl -o all.jsonl
    """
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
            with err_console.status("Fetching all issues..."):
                issues = client.search_all_issues(
                    jql, fields=fields_list, expand=expand_list, max_per_page=None
                )
            total = len(issues)
            is_last = True
            err_console.print(f"[success]{SUCCESS}[/success] Fetched {total} issue(s) total")
        else:
            with err_console.status("Searching issues..."):
                issues, is_last = client.search_issues(
                    jql, max_results=max_results, fields=fields_list, expand=expand_list
                )
            total = len(issues)

        if not issues:
            err_console.print(f"[warning]{WARNING}[/warning] No issues found")
            return

        # Format output based on format option
        if output_format == "json":
            formatted_output = format_as_json(issues)
            if output:
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(formatted_output)

        elif output_format == "csv":
            formatted_output = format_as_csv(issues)
            if output:
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(formatted_output)

        elif output_format == "jsonl":
            formatted_output = format_as_jsonl(issues)
            if output:
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(formatted_output)

        else:  # table (default)
            # Warn if results are truncated
            if not is_last:
                err_console.print(f"[warning]{WARNING}[/warning] Retrieved {total} results (more available — add --all to fetch all)\n")

            # Context line
            err_console.print(f"[muted]Showing {total} results · {jql}[/muted]")

            # Determine active columns
            active_cols = [c.strip().lower() for c in columns.split(",")] if columns else (
                [f.strip().lower() for f in fields.split(",")] if fields else ["key", "type", "status", "summary", "assignee"]
            )

            tbl = Table(box=None, show_edge=False, show_header=not no_headers, header_style="header")
            col_map = {
                "key": ("Key", "key"),
                "type": ("Type", ""),
                "status": ("Status", ""),
                "summary": ("Summary", ""),
                "assignee": ("Assignee", "muted"),
                "priority": ("Priority", ""),
                "updated": ("Updated", "muted"),
                "created": ("Created", "muted"),
            }
            for col in active_cols:
                label, style = col_map.get(col, (col.title(), ""))
                tbl.add_column(label, style=style or None)

            max_summary_width = max(console.width - 60, 30) if not no_truncate else 9999

            for issue in issues:
                f = issue.get("fields", {})
                status_obj = f.get("status") or {}
                status_name = status_obj.get("name", "")
                cat_key = (status_obj.get("statusCategory") or {}).get("key")

                row: list[str] = []
                for col in active_cols:
                    if col == "key":
                        row.append(f"[key]{issue.get('key', '')}[/key]")
                    elif col == "type":
                        row.append((f.get("issuetype") or {}).get("name", ""))
                    elif col == "status":
                        row.append(format_status(status_name, cat_key) if status_name else "")
                    elif col == "summary":
                        s = f.get("summary", "")
                        row.append(s[:max_summary_width] + "…" if len(s) > max_summary_width else s)
                    elif col == "assignee":
                        a = f.get("assignee")
                        row.append(a.get("displayName", "Unassigned") if a else "Unassigned")
                    elif col == "priority":
                        p = f.get("priority")
                        row.append(p.get("name", "") if p else "")
                    elif col in ("updated", "created"):
                        from temet_jira.document.display.formatters import format_date_relative
                        row.append(format_date_relative(f.get(col)))
                    else:
                        row.append(str(f.get(col, "")))
                tbl.add_row(*row)

            if is_interactive() and total > 30:
                with console.pager(styles=True):
                    console.print(tbl)
            else:
                console.print(tbl)

            if output:
                console.print(
                    f"[warning]{WARNING}[/warning] Table format cannot be saved to file. Use --format json, --format csv, or --format jsonl for file output."
                )

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("issue_key")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "jsonl", "csv"]), default=None, help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet. Defaults to config.")
def transitions(issue_key: str, output_format: str | None) -> None:
    """Show available status transitions for an issue.

    Use the transition name with `temet-jira update PROJ-123 --status <name>`.

    \b
    Examples:
        temet-jira transitions PROJ-123
        temet-jira transitions PROJ-123 --format json
    """
    try:
        client = JiraClient()
        effective_fmt = output_format or get_default_format()

        with err_console.status(f"Getting transitions for {issue_key}..."):
            transitions_data = client.get_transitions(issue_key)

        if not transitions_data:
            err_console.print(f"[warning]{WARNING}[/warning] No transitions available")
            return

        if effective_fmt == "json":
            import json as _json
            import sys
            print(_json.dumps(transitions_data, indent=2), file=sys.stdout)
        elif effective_fmt in ("jsonl", "csv"):
            from temet_jira.document.display.formatters import format_as_jsonl, format_as_csv
            rows = [{"id": t["id"], "name": t["name"], "to": (t.get("to") or {}).get("name", "")} for t in transitions_data]
            if effective_fmt == "jsonl":
                import sys
                for row in rows:
                    import json as _json
                    print(_json.dumps(row), file=sys.stdout)
            else:
                import csv, io, sys
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=["id", "name", "to"])
                writer.writeheader()
                writer.writerows(rows)
                print(buf.getvalue(), end="", file=sys.stdout)
        else:
            console.print(f"\n[header]Available transitions for [key]{issue_key}[/key]:[/header]")
            for t in transitions_data:
                status_name = (t.get("to") or {}).get("name", t["name"])
                cat_key = ((t.get("to") or {}).get("statusCategory") or {}).get("key")
                console.print(f"  [muted]{BULLET}[/muted] {format_status(status_name, cat_key)} [muted](ID: {t['id']})[/muted]")

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT env var or config).",
)
@click.option("--format", "output_format", type=click.Choice(["table", "json", "jsonl", "csv"]), default=None, help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet. Defaults to config.")
def types(project: str, output_format: str | None) -> None:
    """List available issue types for a project.

    Use the type name with `temet-jira create --type <name>`.

    \b
    Examples:
        temet-jira types
        temet-jira types --project PROJ
        temet-jira types --format json
    """
    try:
        client = JiraClient()
        effective_fmt = output_format or get_default_format()

        with err_console.status(f"Fetching issue types for {project}..."):
            issue_types = client.get_issue_types(project)

        if not issue_types:
            err_console.print(f"[warning]{WARNING}[/warning] No issue types found for project [key]{project}[/key]")
            return

        from temet_jira.document.builders.profiles import TYPE_PROFILES

        if effective_fmt == "json":
            import json as _json, sys
            print(_json.dumps(issue_types, indent=2), file=sys.stdout)
        elif effective_fmt == "jsonl":
            import json as _json, sys
            for it in issue_types:
                print(_json.dumps(it), file=sys.stdout)
        elif effective_fmt == "csv":
            import csv, io, sys
            rows = [{"name": it.get("name", ""), "subtask": it.get("subtask", False), "has_profile": it.get("name", "").lower() in TYPE_PROFILES} for it in sorted(issue_types, key=lambda x: x.get("name", ""))]
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["name", "subtask", "has_profile"])
            writer.writeheader()
            writer.writerows(rows)
            print(buf.getvalue(), end="", file=sys.stdout)
        else:
            table = Table(title=f"Issue Types — {project}")
            table.add_column("Name", style="key", no_wrap=True)
            table.add_column("Subtask", style="muted")
            table.add_column("Custom Profile", style="success")

            for it in sorted(issue_types, key=lambda x: x.get("name", "")):
                name = it.get("name", "Unknown")
                subtask = "[muted]Yes[/muted]" if it.get("subtask", False) else "No"
                has_profile = "Yes" if name.lower() in TYPE_PROFILES else "No"
                table.add_row(name, subtask, has_profile)

            console.print(table)

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.option("--summary", "-s", help="Issue summary/title")
@click.option("--description", "-d", help="Issue description")
@click.option(
    "--type",
    "-t",
    "issue_type",
    default=None,
    help="Issue type (prompted if omitted and metadata exists)",
)
@click.option("--epic", "-e", help="Epic key to link to (e.g., PROJ-123)")
@click.option("--priority", "-p", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--labels", "-l", help="Comma-separated labels (prompted if omitted and metadata exists)")
@click.option("--component", "-c", help="Component name (prompted if omitted and metadata exists)")
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
def create(
    summary: str | None,
    description: str | None,
    issue_type: str | None,
    epic: str | None,
    priority: str | None,
    labels: str | None,
    component: str | None,
    project: str,
) -> None:
    """Create a new Jira issue.

    Prompts interactively for missing fields when project metadata is available
    (run `temet-jira setup` to fetch component/label/type lists).

    \b
    Examples:
        temet-jira create --summary "Fix login bug" --type Bug
        temet-jira create --summary "New feature" --type Story --priority High
        temet-jira create --summary "Sub-task" --type Task --epic PROJ-10
        temet-jira create --project PROJ
    """
    try:
        meta = load_project_meta(project)
        has_meta = bool(meta)

        if not summary:
            summary = prompt_text("Summary")

        if not issue_type:
            type_choices = meta.get("issue_types", []) if has_meta else []
            if type_choices:
                issue_type = select("Issue type", type_choices) or "Task"
            else:
                issue_type = prompt_text("Issue type", default="Task")

        if not labels and has_meta:
            label_choices = meta.get("labels", [])
            if label_choices:
                chosen_labels = checkbox("Labels", label_choices)
                labels = ",".join(chosen_labels) if chosen_labels else None

        if not component and has_meta:
            comp_choices = meta.get("components", [])
            if comp_choices:
                component = select_optional("Component", comp_choices)

        client = JiraClient()

        label_list = [label.strip() for label in labels.split(",")] if labels else None

        builder = TypedBuilder(issue_type, summary)
        if description:
            builder.add_section_optional("description", text=description)

        fields: dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": builder.build(),
        }

        if priority:
            fields["priority"] = {"name": priority}
        if label_list:
            fields["labels"] = label_list
        if component:
            fields["components"] = [{"name": component}]
        if epic and issue_type.lower() != "epic":
            fields["customfield_10014"] = epic

        with err_console.status(f"Creating {issue_type.lower()} in project {project}..."):
            result = client.create_issue(fields)

        issue_key = result.get("key")
        console.print(f"[success]{SUCCESS}[/success] {issue_type} created successfully: [key]{issue_key}[/key]")

        if issue_key:
            issue = client.get_issue(issue_key)
            format_issue(issue)

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
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
    help=f"Maximum number of epics to show (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()}).",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default=get_default_format(),
    help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet.",
)
@click.option("--output", "-o", help="Output file path (optional).")
@click.option("--columns", help="Table columns to display, comma-separated. Available: key,summary,status,assignee,updated,priority")
@click.option("--no-truncate", is_flag=True, default=False, help="Do not truncate long values.")
@click.option("--no-headers", is_flag=True, default=False, help="Omit table headers (useful for scripting).")
def epics(project: str, max_results: int | None, output_format: str, output: str | None, columns: str | None, no_truncate: bool, no_headers: bool) -> None:
    """List all epics in a project.

    \b
    Examples:
        temet-jira epics
        temet-jira epics --project PROJ
        temet-jira epics --format csv -o epics.csv
        temet-jira epics --columns key,summary,status,assignee
    """
    try:
        client = JiraClient()

        with err_console.status(f"Fetching epics for project {project}..."):
            issues = client.get_epics(project, max_results)

        if not issues:
            err_console.print(f"[warning]{WARNING}[/warning] No epics found in project [key]{project}[/key]")
            return

        if output_format == "json":
            result = format_as_json(issues)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        elif output_format == "csv":
            result = format_as_csv(issues)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        elif output_format == "jsonl":
            result = format_as_jsonl(issues)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        else:
            err_console.print(f"[muted]Found {len(issues)} epics in {project}[/muted]")
            col_list = [c.strip() for c in columns.split(",")] if columns else None
            format_issues_table(issues, columns=col_list, no_truncate=no_truncate, show_headers=not no_headers)

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.command()
@click.argument("epic_key")
@click.option(
    "--show-children", "-c", is_flag=True, help="Include child issues of the epic in the output."
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default=get_default_format(),
    help="Output format: table=console, json=readable, jsonl=streaming, csv=spreadsheet.",
)
@click.option("--output", "-o", help="Output file path (optional).")
@click.option("--web", is_flag=True, default=False, help="Open the epic in your browser instead of displaying it.")
def epic_details(
    epic_key: str, show_children: bool, output_format: str, output: str | None, web: bool
) -> None:
    """Get detailed information about an epic, including its child issues.

    \b
    Examples:
        temet-jira epic-details PROJ-10
        temet-jira epic-details PROJ-10 --show-children
        temet-jira epic-details PROJ-10 --show-children --format json -o epic.json
        temet-jira epic-details PROJ-10 --web
    """
    try:
        client = JiraClient()

        if web:
            import webbrowser
            webbrowser.open(f"{client.server_url}/browse/{epic_key}")
            return

        with err_console.status(f"Fetching epic {epic_key}..."):
            epic = client.get_issue(epic_key)

        children: list[dict[str, Any]] = []
        if show_children:
            with err_console.status("Fetching child issues..."):
                try:
                    children, _ = client.search_issues(
                        f"parent = {epic_key}", max_results=100
                    )
                except Exception:
                    try:
                        epic_link_field = client.get_epic_link_field()
                        if epic_link_field:
                            children, _ = client.search_issues(
                                f"{epic_link_field} = {epic_key}", max_results=100
                            )
                        else:
                            children, _ = client.search_issues(
                                f'"Epic Link" = {epic_key}', max_results=100
                            )
                    except Exception:
                        console.print(
                            f"[warning]{WARNING}[/warning] Unable to fetch child issues - epic link field may not be available"
                        )

        if output_format == "json":
            payload: list[dict[str, Any]] = [epic] + children
            result = format_as_json(payload)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        elif output_format == "csv":
            payload = [epic] + children
            result = format_as_csv(payload)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        elif output_format == "jsonl":
            payload = [epic] + children
            result = format_as_jsonl(payload)
            if output:
                Path(output).write_text(result)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(result)
        else:
            format_issue(epic)
            if show_children:
                if children:
                    console.print(f"\n[header]Child Issues:[/header] [muted]({len(children)} found)[/muted]")
                    format_issues_table(children)
                else:
                    console.print(f"[warning]{WARNING}[/warning] No child issues found")

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
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
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default=get_default_format(),
    help="Output format: table=console, json=readable, jsonl=streaming/pipes, csv=spreadsheet.",
)
@click.option(
    "--output", "-o", help="Output file path (required when saving json/csv/jsonl to disk)."
)
@click.option("--stats", is_flag=True, help="Display summary statistics (by status, priority, type, assignee).")
@click.option(
    "--group-by",
    type=click.Choice(["status", "assignee", "priority"], case_sensitive=False),
    help="Group results by the specified field.",
)
@click.option(
    "--expand",
    help="Comma-separated fields to expand, e.g. changelog,transitions. Required for state-duration analysis.",
)
@click.option(
    "--limit",
    "-n",
    default=None,
    type=int,
    help=f"Maximum number of results (defaults to JIRA_DEFAULT_MAX_RESULTS env var, currently: {_get_default_max_results()}).",
)
@click.option(
    "--all", "fetch_all", is_flag=True, help="Fetch every page of results (can be slow for large projects)."
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

    \b
    Priority: CLI flag > config file > env var > default

    \b
    Examples:
        # Default project (from config or JIRA_DEFAULT_PROJECT)
        temet-jira export --format csv -o tickets.csv
        # Specific project
        temet-jira export --project PROJ --format csv -o tickets.csv
        # All tickets, streaming JSONL (good for large datasets)
        temet-jira export -p PROJ --all --format jsonl -o all_tickets.jsonl
        # High priority tickets with statistics
        temet-jira export --priority High --stats
        # Tickets grouped by assignee
        temet-jira export --status "In Progress" --group-by assignee
        # Custom JQL
        temet-jira export --jql "assignee = currentUser()" --format json -o my_tickets.json
        # With changelog (required for state-duration analysis)
        temet-jira export -p PROJ --expand changelog --format json -o issues.json
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

        err_console.print(f"[muted]Query: {jql_query}[/muted]\n")

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
            with err_console.status("Fetching all issues..."):
                issues = client.search_all_issues(
                    jql_query, fields=fields, expand=expand_list, max_per_page=limit
                )
            err_console.print(f"[success]{SUCCESS}[/success] Fetched {len(issues)} issue(s) total\n")
            is_last = True
        else:
            with err_console.status("Fetching issues..."):
                issues, is_last = client.search_issues(
                    jql_query, fields=fields, expand=expand_list, max_results=limit
                )

            if not is_last:
                err_console.print(
                    f"[warning]{WARNING}[/warning] Retrieved {len(issues)} results (more available — add --all to fetch all)\n"
                )
            else:
                err_console.print(f"[success]{SUCCESS}[/success] Fetched {len(issues)} issue(s)\n")

        if not issues:
            err_console.print(f"[warning]{WARNING}[/warning] No issues found matching the criteria.")
            return

        # Display statistics if requested
        if stats:
            by_status: defaultdict[str, int] = defaultdict(int)
            by_priority: defaultdict[str, int] = defaultdict(int)
            by_assignee: defaultdict[str, int] = defaultdict(int)
            by_type: defaultdict[str, int] = defaultdict(int)

            for issue in issues:
                fields_data = issue.get("fields", {})
                issue_status = (fields_data.get("status") or {}).get("name", "Unknown")
                issue_priority = (fields_data.get("priority") or {}).get("name", "Unknown")
                issue_issuetype = (fields_data.get("issuetype") or {}).get(
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
                    key = (fields_data.get("status") or {}).get("name", "Unknown")
                elif group_by == "assignee":
                    assignee_obj = fields_data.get("assignee")
                    key = (
                        assignee_obj.get("displayName", "Unassigned")
                        if assignee_obj
                        else "Unassigned"
                    )
                elif group_by == "priority":
                    key = (fields_data.get("priority") or {}).get("name", "Unknown")
                else:
                    key = "Unknown"

                groups[key].append(issue)

            console.print(f"[header]GROUPED BY {group_by.upper()}[/header]\n")

            for group_key in sorted(groups.keys()):
                items = groups[group_key]
                console.print(f"[key]{group_key}[/key] [muted]({len(items)} issues):[/muted]")

                for issue in items:
                    issue_key_val = issue.get("key")
                    summary_text = issue.get("fields", {}).get("summary", "")[:70]
                    status_obj = issue.get("fields", {}).get("status", {})
                    issue_status = status_obj.get("name", "")
                    cat_key = (status_obj.get("statusCategory") or {}).get("key")
                    console.print(f"  [key]{issue_key_val}[/key]  {summary_text}  {format_status(issue_status, cat_key)}")

                console.print()

        # Handle output format
        if output_format == "json":
            if not output and not stats and not group_by:
                formatted_output = format_as_json(issues, indent=2)
                click.echo(formatted_output)
            elif output:
                formatted_output = format_as_json(issues, indent=2)
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Exported {len(issues)} issues to {output}")
            else:
                console.print(f"[info]{INFO}[/info] Use --output/-o to save JSON to file")

        elif output_format == "csv":
            if not output:
                if not stats and not group_by:
                    formatted_output = format_as_csv(issues)
                    click.echo(formatted_output)
                else:
                    console.print(f"[error]{FAILURE}[/error] --output/-o is required for CSV format when using --stats or --group-by")
                    raise click.Abort()
            else:
                formatted_output = format_as_csv(issues)
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Exported {len(issues)} issues to {output}")

        elif output_format == "jsonl":
            if not output and not stats and not group_by:
                formatted_output = format_as_jsonl(issues)
                click.echo(formatted_output)
            elif output:
                formatted_output = format_as_jsonl(issues)
                Path(output).write_text(formatted_output)
                console.print(f"[success]{SUCCESS}[/success] Exported {len(issues)} issues to {output}")
            else:
                console.print(f"[info]{INFO}[/info] Use --output/-o to save JSONL to file")

        else:  # table format (default)
            if output:
                console.print(
                    f"[warning]{WARNING}[/warning] Table format cannot be saved to file. Use --format json, --format csv, or --format jsonl for file output."
                )

            if not stats and not group_by:
                err_console.print(f"[muted]Total: {len(issues)} issue(s)[/muted]")
                format_issues_table(issues)

    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] {str(e)}")
        raise click.Abort() from e


@jira.group(name="analyze", cls=_HelpAwareGroup)
def analyze() -> None:
    """Analyze Jira issues and generate reports.

    \b
    Typical workflow for state-duration analysis:
        1. Export issues with changelog:
               temet-jira export PROJ --expand changelog --format json -o issues.json
        2. Analyze state durations:
               temet-jira analyze state-durations issues.json -o durations.csv
    """
    pass


@analyze.command(name="state-durations")
@click.argument(
    "input_file", type=click.Path(exists=True, readable=True, path_type=Path)
)
@click.option(
    "--output",
    "-o",
    required=False,
    default=None,
    type=click.Path(path_type=Path),
    help="Output file path (prints to console if omitted).",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "jsonl", "csv"], case_sensitive=False),
    default="csv",
    help="Output format: csv=spreadsheet (default), table=console, json=readable, jsonl=streaming.",
)
@click.option("--date-from", help="Only include issues created on or after this date (YYYY-MM-DD).")
@click.option("--date-to", help="Only include issues created on or before this date (YYYY-MM-DD).")
@click.option("--business-hours", is_flag=True, help="Calculate durations in business hours (9 AM–5 PM, weekdays).")
@click.option(
    "--timezone", default="UTC", help="Timezone for business-hours calculations (default: UTC)."
)
def state_durations(
    input_file: Path,
    output: Path | None,
    output_format: str,
    date_from: str | None,
    date_to: str | None,
    business_hours: bool,
    timezone: str,
) -> None:
    """Analyze time spent in each workflow state, from a JSON export.

    The input file must be a JSON array of Jira issues exported with
    `--expand changelog` (use `temet-jira export ... --expand changelog`).

    \b
    Examples:
        temet-jira analyze state-durations sprint_issues.json -o durations.csv
        temet-jira analyze state-durations sprint_issues.json --format json
        temet-jira analyze state-durations sprint_issues.json --business-hours --timezone Europe/London
        temet-jira analyze state-durations sprint_issues.json --date-from 2024-01-01 --date-to 2024-03-31
    """
    try:
        # Read the JSON file
        with err_console.status(f"Reading issues from {input_file}..."):
            try:
                with open(input_file) as f:
                    issues_data = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[error]{FAILURE}[/error] Invalid JSON file: {e}")
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
            console.print(f"[warning]{WARNING}[/warning] No issues found in input file")
            if output:
                with open(Path(output), "w", newline="") as f:
                    csv.writer(f).writerow(
                        ["issue_key", "summary", "current_status", "created", "updated"]
                    )
                console.print(f"[success]{SUCCESS}[/success] Empty results saved to {output}")
            return

        console.print(f"[muted]Found {len(issues_data)} issue(s) to analyze[/muted]")

        # Filter by date range if specified
        filtered_issues = issues_data
        if date_from or date_to:
            filtered_issues = []
            try:
                date_from_obj = (
                    datetime.fromisoformat(date_from + "T00:00:00+00:00")
                    if date_from
                    else None
                )
                date_to_obj = (
                    datetime.fromisoformat(date_to + "T23:59:59+00:00") if date_to else None
                )
            except ValueError as e:
                console.print(f"[error]{FAILURE}[/error] Error: Invalid date format — use YYYY-MM-DD. Got: {e}")
                raise click.Abort() from e

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
                f"[muted]After date filtering: {len(filtered_issues)} issue(s)[/muted]"
            )

        # Initialize the analyzer
        analyzer = StateDurationAnalyzer()

        # Process issues with progress indicator for large datasets
        if len(filtered_issues) > 50:
            console.print("[muted]Processing large dataset...[/muted]")
            with err_console.status("Analyzing state durations..."):
                try:
                    if business_hours:
                        if hasattr(analyzer, "analyze_issues_business_hours"):
                            results = analyzer.analyze_issues_business_hours(
                                filtered_issues, timezone=timezone
                            )
                        else:
                            results = analyzer.analyze_issues(filtered_issues)
                            console.print(
                                f"[info]{INFO}[/info] Business hours calculation not yet implemented"
                            )
                    else:
                        results = analyzer.analyze_issues(filtered_issues)
                except NotImplementedError:
                    console.print(
                        f"[info]{INFO}[/info] State analysis not fully implemented, generating basic output"
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
                        results = analyzer.analyze_issues(filtered_issues)
                        console.print(
                            f"[info]{INFO}[/info] Business hours calculation not yet implemented"
                        )
                else:
                    results = analyzer.analyze_issues(filtered_issues)
            except NotImplementedError:
                console.print(
                    f"[info]{INFO}[/info] State analysis not fully implemented, generating basic output"
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

        # Build CSV string (shared by both csv format and table fallback)
        def _build_csv(rows: list[dict[str, Any]]) -> str:
            import io

            buf = io.StringIO()
            fieldnames: list[str] = [
                "issue_key", "summary", "current_status", "created", "updated",
            ]
            if rows:
                all_states: set[str] = set()
                for r in rows:
                    if isinstance(r.get("state_durations"), dict):
                        all_states.update(r["state_durations"].keys())
                for state in sorted(all_states):
                    fieldnames.append(f"duration_{state}")

            writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                row: dict[str, Any] = {
                    "issue_key": r.get("issue_key", ""),
                    "summary": r.get("summary", ""),
                    "current_status": r.get("current_status", ""),
                    "created": r.get("created", ""),
                    "updated": r.get("updated", ""),
                }
                if isinstance(r.get("state_durations"), dict):
                    for state, duration in r["state_durations"].items():
                        row[f"duration_{state}"] = duration
                writer.writerow(row)
            return buf.getvalue()

        # Prefer analyzer's own CSV formatter when it supports durations
        def _get_csv(rows: list[dict[str, Any]]) -> str:
            if rows and "durations" in rows[0]:
                return analyzer.format_as_csv(rows, include_business_hours=business_hours)
            return _build_csv(rows)

        def _write(text: str) -> None:
            if output:
                Path(output).write_text(text)
                console.print(f"[success]{SUCCESS}[/success] Results saved to {output}")
            else:
                click.echo(text)

        console.print(f"[success]{SUCCESS}[/success] Analyzed {len(results)} issue(s)")

        if output_format == "csv":
            _write(_get_csv(results))

        elif output_format == "json":
            _write(json.dumps(results, indent=2, default=str))

        elif output_format == "jsonl":
            _write("\n".join(json.dumps(r, default=str) for r in results))

        else:  # table
            all_states_t: list[str] = []
            if results:
                seen: set[str] = set()
                for r in results:
                    if isinstance(r.get("state_durations"), dict):
                        for s in r["state_durations"]:
                            if s not in seen:
                                seen.add(s)
                                all_states_t.append(s)

            tbl = Table(show_header=True, header_style="header")
            tbl.add_column("Key", style="key")
            tbl.add_column("Summary")
            tbl.add_column("Status")
            for s in sorted(all_states_t):
                tbl.add_column(s)

            for r in results:
                durations = r.get("state_durations") or {}
                tbl.add_row(
                    r.get("issue_key", ""),
                    r.get("summary", ""),
                    r.get("current_status", ""),
                    *[str(durations.get(s, "")) for s in sorted(all_states_t)],
                )
            console.print(tbl)
            if output:
                console.print(
                    f"[warning]{WARNING}[/warning] Table format cannot be saved to file — "
                    "use --format csv, json, or jsonl for file output."
                )

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] Unexpected error: {e}")
        raise click.Abort() from e


# =============================================================================
# Configuration Commands
# =============================================================================


def _scan_env_suggestions() -> dict[str, list[tuple[str, str]]]:
    """Scan environment for JIRA_* / ATLASSIAN_* vars that could fill each field.

    Returns a dict mapping field name → list of (VAR_NAME, partial_value) tuples.
    Standard vars (JIRA_BASE_URL etc.) are excluded since they're already auto-picked.
    """
    _STANDARD = {"JIRA_BASE_URL", "JIRA_USERNAME", "JIRA_API_TOKEN",
                 "JIRA_DEFAULT_PROJECT", "JIRA_DEFAULT_COMPONENT",
                 "JIRA_DEFAULT_MAX_RESULTS", "JIRA_DEFAULT_FORMAT"}
    url_re = re.compile(r"url|base", re.I)
    user_re = re.compile(r"user|email|login", re.I)
    token_re = re.compile(r"token|key|secret", re.I)

    suggestions: dict[str, list[tuple[str, str]]] = {"base_url": [], "username": [], "api_token": []}

    for var, val in sorted(os.environ.items()):
        if var in _STANDARD:
            continue
        if not (var.startswith("JIRA_") or var.startswith("ATLASSIAN_")):
            continue
        if not val:
            continue
        preview = val if len(val) <= 30 else val[:27] + "…"
        if url_re.search(var) and val.startswith("https://"):
            suggestions["base_url"].append((var, preview))
        elif user_re.search(var) and "@" in val:
            suggestions["username"].append((var, preview))
        elif token_re.search(var) and len(val) > 20:
            suggestions["api_token"].append((var, val[:4] + "****"))
    return suggestions


def _prompt_with_env_suggestions(
    field: str,
    suggestions: list[tuple[str, str]],
    prompt_label: str,
    current: str | None = None,
    password: bool = False,
) -> str:
    """Prompt for a value, offering env var references when suggestions exist."""
    if suggestions:
        console.print(f"[muted]Found in your environment:[/muted]")
        for var, preview in suggestions:
            console.print(f"  [key]${{{var}}}[/key]  [muted]{preview}[/muted]")
        console.print()
        choices = [f"${{{var}}}" for var, _ in suggestions] + ["Enter a value manually"]
        choice = select(f"Use an env var reference or enter manually?", choices)
        if choice and not choice.startswith("Enter"):
            return choice
    return prompt_text(prompt_label, default=current or "", password=password)


@jira.command()
def setup() -> None:
    """Interactive setup wizard for temet-jira.

    Guides you through configuring Jira credentials and saves them to
    ~/.config/temet-jira/config.yaml.

    \b
    You will be prompted for:
      - Jira instance URL  (e.g. https://company.atlassian.net)
      - Email address
      - API token  — generate one at:
            https://id.atlassian.com/manage-profile/security/api-tokens
      - Default project key (optional)

    \b
    Values can reference environment variables using ${VAR_NAME} syntax
    (e.g. ${MY_JIRA_TOKEN}), so secrets stay in your environment and
    are not stored literally in the config file.

    \b
    Example:
        temet-jira setup
    """
    console.print()
    console.print(
        Panel.fit(
            "[info]temet-jira Setup[/info]\n\n"
            "This will help you configure temet-jira with your Jira credentials.\n"
            f"Configuration will be saved to: [key]{get_config_path()}[/key]",
            border_style="blue",
        )
    )
    console.print()

    # Check if already configured
    if is_configured():
        console.print(f"[warning]{WARNING}[/warning] temet-jira is already configured.")
        console.print()
        existing = get_all_config()
        console.print("[muted]Current configuration:[/muted]")
        for key, value in existing.items():
            if value:
                console.print(f"  {key}: {mask_sensitive(value, key)}")
        console.print()

        if not confirm("Reconfigure?", default=False):
            console.print("[muted]Setup cancelled.[/muted]")
            return

    env_suggestions = _scan_env_suggestions()
    has_any_suggestions = any(v for v in env_suggestions.values())

    if has_any_suggestions:
        console.print(
            f"[success]{SUCCESS}[/success] Found Jira-related environment variables — "
            "you can store references (e.g. [key]${{JIRA_TEMET_JIRA_URL}}[/key]) "
            "instead of literal values."
        )
        console.print()

    console.print("[header]Step 1: Jira Instance URL[/header]")
    console.print("[muted]This is your Jira Cloud URL (e.g., https://company.atlassian.net)[/muted]")
    console.print()

    current_url = get_value("base_url")
    base_url = _prompt_with_env_suggestions("base_url", env_suggestions["base_url"], "Jira URL", current=current_url)

    if not base_url.startswith("${"):
        if not base_url.startswith("https://"):
            console.print(f"[warning]{WARNING}[/warning] URL should start with https://")
            if not base_url.startswith("http"):
                base_url = "https://" + base_url
        base_url = base_url.rstrip("/")

    console.print()
    console.print("[header]Step 2: Your Email Address[/header]")
    console.print("[muted]The email you use to log into Jira[/muted]")
    console.print()

    current_username = get_value("username")
    username = _prompt_with_env_suggestions("username", env_suggestions["username"], "Email", current=current_username)

    console.print()
    console.print("[header]Step 3: API Token[/header]")
    console.print("[muted]Generate at: https://id.atlassian.com/manage-profile/security/api-tokens[/muted]")
    console.print("[muted]The token will be stored securely and masked in displays.[/muted]")
    console.print()

    api_token = _prompt_with_env_suggestions("api_token", env_suggestions["api_token"], "API Token", password=True)

    if not api_token:
        console.print(f"[error]{FAILURE}[/error] API token is required")
        raise click.Abort()

    console.print()
    console.print("[header]Step 4: Project (Optional)[/header]")
    console.print("[muted]Set a project key to avoid typing --project every time[/muted]")

    current_project = get_value("project")
    project = prompt_text("Project key", default=current_project or "")

    # Save configuration
    console.print()
    console.print("[muted]Saving configuration...[/muted]")

    try:
        set_value("base_url", base_url)
        set_value("username", username)
        set_value("api_token", api_token)
        if project:
            set_value("project", project)

        console.print(f"[success]{SUCCESS}[/success] Configuration saved to {get_config_path()}")
    except Exception as e:
        console.print(f"[error]{FAILURE}[/error] Error saving configuration: {e}")
        raise click.Abort() from e

    # Test the connection — resolve any ${VAR} references before connecting
    from .config import _interpolate
    resolved_url = _interpolate(base_url)
    resolved_user = _interpolate(username)
    resolved_token = _interpolate(api_token)

    console.print()
    console.print("[muted]Testing connection...[/muted]")

    try:
        client = JiraClient(
            base_url=resolved_url,
            username=resolved_user,
            api_token=resolved_token,
        )
        # Try to get current user info
        response = client.session.get(f"{resolved_url}/rest/api/3/myself")
        if response.status_code == 200:
            user_data = response.json()
            display_name = user_data.get("displayName", username)
            console.print(f"[success]{SUCCESS}[/success] Connected successfully as [bold]{display_name}[/bold]")
        else:
            console.print(f"[warning]{WARNING}[/warning] Connection test returned status {response.status_code}")
            console.print("[muted]Configuration saved, but you may need to verify your credentials.[/muted]")
    except Exception as e:
        console.print(f"[warning]{WARNING}[/warning] Connection test failed: {e}")
        console.print("[muted]Configuration saved, but please verify your credentials.[/muted]")

    # Step 5: Optional project metadata (components, labels, issue types)
    if project:
        console.print()
        console.print("[header]Step 5: Project Metadata (Optional)[/header]")
        console.print(
            f"[muted]Fetches components, labels, and issue types used in "
            f"{project} — enables interactive prompts in 'create'.[/muted]"
        )
        if confirm("Fetch project metadata now?", default=True):
            try:
                fetch_client = JiraClient(base_url=resolved_url, username=resolved_user, api_token=resolved_token)
                with err_console.status(f"Fetching metadata for [bold]{project}[/bold]..."):
                    try:
                        components = fetch_client.get_components(project)
                    except Exception:
                        components = []
                    try:
                        issue_types = fetch_client.get_issue_types(project)
                    except Exception:
                        issue_types = []
                    try:
                        labels = fetch_client.get_labels_used(project)
                    except Exception:
                        labels = []

                component_names = [c.get("name", "") for c in components if c.get("name")]
                type_names = [
                    t.get("name", "") for t in issue_types
                    if t.get("name") and not t.get("subtask")
                ]
                meta = {
                    "project": project,
                    "discovered_at": datetime.now().strftime("%Y-%m-%d"),
                    "components": component_names,
                    "labels": labels,
                    "issue_types": type_names,
                }
                meta_path = save_project_meta(project, meta)
                console.print(f"[success]{SUCCESS}[/success] Saved to [muted]{meta_path}[/muted]")
                if component_names:
                    rest = f" (+{len(component_names)-5} more)" if len(component_names) > 5 else ""
                    console.print(f"  Components:   {', '.join(component_names[:5])}{rest}")
                if type_names:
                    rest = f" (+{len(type_names)-8} more)" if len(type_names) > 8 else ""
                    console.print(f"  Issue types:  {', '.join(type_names[:8])}{rest}")
                if labels:
                    rest = f" (+{len(labels)-8} more)" if len(labels) > 8 else ""
                    console.print(f"  Labels:       {', '.join(labels[:8])}{rest}")
            except Exception as e:
                console.print(f"[warning]{WARNING}[/warning] Metadata fetch failed: {e}")
                console.print("[muted]You can re-run setup later to fetch project metadata.[/muted]")

    console.print()
    console.print(f"[success]Setup complete![/success]")
    console.print()
    console.print("Try these commands:")
    console.print("  [key]temet-jira config[/key]        - View your configuration")
    if project:
        console.print(f"  [key]temet-jira export[/key]        - Export tickets from {project}")
    console.print("  [key]temet-jira search \"status = Open\"[/key]  - Search for issues")
    console.print()


@jira.group(name="config", cls=_HelpAwareGroup)
def config_cmd() -> None:
    """View and manage temet-jira configuration.

    \b
    Config file: ~/.config/temet-jira/config.yaml
    Priority:    CLI flag > config file > env var > default

    \b
    Valid keys: base_url, username, api_token, project, component,
                max_results, default_format
    """
    pass


@config_cmd.command(name="show")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default=None, help="Output format: table=console, json=machine-readable. Defaults to config.")
def config_show(fmt: str | None) -> None:
    """Show current configuration.

    Sensitive values (api_token) are masked with asterisks for security.

    \b
    Examples:
        temet-jira config show
        temet-jira config show --format json
    """
    from .config import get_default_format
    effective_fmt = fmt or (get_default_format() if get_default_format() in ("table", "json") else "table")

    config = get_all_config()

    if not any(v for v in config.values()):
        console.print("[yellow]No configuration found.[/yellow]")
        console.print(f"[dim]Config file: {get_config_path()}[/dim]")
        console.print()
        console.print("Run [cyan]temet-jira setup[/cyan] to configure.")
        return

    if effective_fmt == "json":
        import json as _json
        import sys
        output = {key: mask_sensitive(value, key) for key, value in config.items()}
        print(_json.dumps(output, indent=2), file=sys.stdout)
        return

    table = Table(title="temet-jira Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    for key, value in config.items():
        table.add_row(key, mask_sensitive(value, key))

    console.print(table)
    console.print()
    console.print(f"[dim]Config file: {get_config_path()}[/dim]")


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    \b
    Valid keys:
        base_url        Jira instance URL (e.g. https://company.atlassian.net)
        username        Email address used to log into Jira
        api_token       API token — generate at:
                            https://id.atlassian.com/manage-profile/security/api-tokens
        project         Default project key (e.g. PROJ)
        component       Default component filter
        max_results     Default max results per query (default: 300)
        default_format  Default output format (table|json|jsonl|csv)

    \b
    Values can reference environment variables — all of these forms are accepted
    and stored as a ${VAR} reference resolved at runtime:
        $VAR_NAME           bare dollar sign (use single quotes to prevent shell expansion)
        ${VAR_NAME}         braced form
        '$JIRA_BASE_URL'    single-quoted to pass literally

    \b
    Examples:
        temet-jira config set project PROJ
        temet-jira config set default_format csv
        temet-jira config set api_token '$MY_JIRA_TOKEN'
        temet-jira config set base_url '$JIRA_BASE_URL'
        temet-jira config set base_url '${JIRA_BASE_URL}'
    """
    value, env_var_name = normalize_env_ref(value)
    if not value.strip():
        console.print(f"[red]Error:[/red] Value for '{key}' is empty — did you mean to pass an environment variable that isn't set?")
        console.print(f"[dim]Tip: temet-jira config set {key} '${{MY_VAR}}'  (stores as reference, resolved at runtime)[/dim]")
        raise click.Abort()
    if env_var_name and env_var_name not in os.environ:
        console.print(f"[yellow]Warning:[/yellow] ${{{env_var_name}}} is not set in the current environment — value will be stored as a reference and resolved at runtime.")
    try:
        set_value(key, value)
        display_value = mask_sensitive(value, key)
        if env_var_name:
            console.print(f"[green]✓[/green] Set {key} = {display_value}  [dim](resolved at runtime from ${{{env_var_name}}})[/dim]")
        else:
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
    """Get a single configuration value.

    Prints the resolved value (env-var references are NOT expanded here —
    use `temet-jira config show` to see all values with their sources).

    \b
    Examples:
        temet-jira config get base_url
        temet-jira config get project
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
    """Remove a configuration value from the config file.

    If the corresponding env var (e.g. JIRA_DEFAULT_PROJECT) is still set,
    it will continue to be used after unsetting.

    \b
    Examples:
        temet-jira config unset project
        temet-jira config unset default_format
    """
    if delete_value(key):
        console.print(f"[green]✓[/green] Removed {key}")
    else:
        console.print(f"[yellow]{key} was not set in config file[/yellow]")


@config_cmd.command(name="path")
def config_path() -> None:
    """Show the path to the config file.

    \b
    Example:
        temet-jira config path
    """
    path = get_config_path()
    console.print(str(path))
    if config_exists():
        console.print("[dim](file exists)[/dim]")
    else:
        console.print("[dim](file does not exist)[/dim]")


@config_cmd.command(name="edit")
def config_edit() -> None:
    """Open the config file in your default editor.

    Uses the $EDITOR environment variable (falls back to nano if not set).

    \b
    Example:
        temet-jira config edit
    """
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


@jira.group(name="mcp", cls=_HelpAwareGroup)
def mcp_cmd() -> None:
    """Manage MCP server configuration for AI assistants.

    MCP (Model Context Protocol) lets AI assistants like Claude interact
    with temet-jira directly. Use `mcp add` to get the config snippet for
    your IDE, and `mcp tools` to see which tools are exposed.
    """


@mcp_cmd.command(name="add")
def mcp_add() -> None:
    """Generate the MCP config snippet for your IDE or AI client.

    Scans common config file locations (Claude Code, Cursor, VS Code, Zed,
    Windsurf) and guides you to the right JSON snippet to paste.

    MCP (Model Context Protocol) enables AI assistants to call temet-jira
    tools directly from the chat interface.

    \b
    Example:
        temet-jira mcp add
    """

    console.print("\n[header]temet-jira MCP setup[/header]\n")

    # Detect which config files already exist
    detected: list[int] = []
    for i, (_label, path_str, _, _) in enumerate(_MCP_TARGETS[:-1]):
        if path_str and Path(path_str).expanduser().exists():
            detected.append(i)

    # Check if global Claude config (index 0) is among detected
    global_detected = 0 in detected
    local_detected = 1 in detected

    if detected:
        console.print("[success]Already configured in:[/success]")
        for i in detected:
            label, _, _, _ = _MCP_TARGETS[i]
            console.print(f"  [success]{SUCCESS}[/success] {label}")

        if global_detected and local_detected:
            console.print(
                f"\n[warning]{WARNING}[/warning] The global config already covers all projects — "
                "the project-level config is redundant."
            )

        console.print(
            f"\n[muted]Run [key]temet-jira mcp tools[/key] for the list of available tools.[/muted]"
        )
        console.print()
        if not confirm("Add snippet for another client too?", default=False):
            return

    # Build choice list
    client_names = []
    for i, (label, _path_str, _, _) in enumerate(_MCP_TARGETS):
        already = " (already configured)" if i in detected else ""
        client_names.append(f"{label}{already}")

    default_client = client_names[detected[0]] if detected else client_names[0]
    chosen_client = select("Which client do you want the config snippet for?", client_names, default=default_client)
    if chosen_client is None:
        return

    choice = client_names.index(chosen_client)
    label, path_str, json_key, fmt = _MCP_TARGETS[choice]

    # Check if env vars are already set
    has_env = all(
        os.environ.get(k)
        for k in ("JIRA_BASE_URL", "JIRA_USERNAME", "JIRA_API_TOKEN")
    )
    if has_env:
        console.print(
            f"\n[success]{SUCCESS}[/success] JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN are set in your "
            "environment — the [bold]env[/bold] block is optional.\n"
        )
        include_env = confirm("Include env block in snippet anyway?", default=False)
    else:
        include_env = True

    snippet = _build_snippet(json_key, fmt, include_env)

    # Show target file guidance
    if path_str:
        target = Path(path_str).expanduser()
        exists = target.exists()
        console.print(f"\n[header]File:[/header] [key]{target}[/key]")
        if exists:
            console.print(
                f"[muted]{CHILD} File exists — merge the snippet into the "
                f'existing [header]"{json_key}"[/header] object.[/muted]'
            )
        else:
            console.print(
                f"[warning]{WARNING}[/warning] File does not exist — create it with the content below."
            )

    console.print("\n[header]Paste this into your config:[/header]\n")

    if path_str and not Path(path_str).expanduser().exists():
        full = "{\n  " + snippet + "\n}"
        console.print(f"[muted]# {Path(path_str).expanduser()}[/muted]")
        console.print(full)
    else:
        console.print("[muted]# merge into your existing JSON[/muted]")
        console.print("{")
        console.print("  // ... your existing config ...")
        console.print("  " + snippet.replace("\n", "\n  "))
        console.print("}")

    console.print(
        f"\n[muted]Run [key]temet-jira mcp tools[/key] to see the list of available MCP tools.[/muted]\n"
    )


@mcp_cmd.command(name="tools")
def mcp_tools() -> None:
    """List all tools exposed by the temet-jira MCP server.

    These tools are available to AI assistants (e.g. Claude) once MCP
    is configured. Use `temet-jira mcp add` to set up the config snippet.

    \b
    Example:
        temet-jira mcp tools
    """
    table = Table(title="temet-jira MCP Tools", show_header=True, header_style="header")
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
