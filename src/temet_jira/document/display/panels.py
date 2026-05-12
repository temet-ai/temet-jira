"""Rich Panel builders for displaying Jira issues."""

import re
from typing import Any, Self

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from temet_jira.document.adf import extract_text_from_adf
from temet_jira.document.display.formatters import (
    format_date,
    format_date_relative,
    get_priority,
    get_user_display,
)

console = Console()


class IssuePanelBuilder:
    """Builder for creating Rich Panels displaying Jira issue details."""

    def __init__(self, issue: dict[str, Any]) -> None:
        """Initialize with issue data."""
        self._issue = issue
        self._fields = issue.get("fields", {})
        self._lines: list[str] = []

    def add_key(self) -> Self:
        """Add issue key line."""
        self._lines.append(f"[bold]Issue:[/bold] {self._issue.get('key', 'N/A')}")
        return self

    def add_summary(self) -> Self:
        """Add summary line."""
        summary = self._fields.get("summary", "No summary")
        self._lines.append(f"[bold]Summary:[/bold] {summary}")
        return self

    def add_status(self) -> Self:
        """Add status line."""
        status = self._fields.get("status", {}).get("name", "Unknown")
        self._lines.append(f"[bold]Status:[/bold] {status}")
        return self

    def add_priority(self) -> Self:
        """Add priority line."""
        priority = get_priority(self._fields)
        self._lines.append(f"[bold]Priority:[/bold] {priority}")
        return self

    def add_type(self) -> Self:
        """Add issue type line."""
        issue_type = self._fields.get("issuetype", {}).get("name", "Unknown")
        self._lines.append(f"[bold]Type:[/bold] {issue_type}")
        return self

    def add_assignee(self) -> Self:
        """Add assignee line."""
        assignee = get_user_display(self._fields.get("assignee"))
        self._lines.append(f"[bold]Assignee:[/bold] {assignee}")
        return self

    def add_reporter(self) -> Self:
        """Add reporter line."""
        reporter = get_user_display(self._fields.get("reporter"))
        self._lines.append(f"[bold]Reporter:[/bold] {reporter}")
        return self

    def add_created(self) -> Self:
        """Add created date line."""
        created = format_date(self._fields.get("created"))
        self._lines.append(f"[bold]Created:[/bold] {created}")
        return self

    def add_updated(self) -> Self:
        """Add updated date line."""
        updated = format_date(self._fields.get("updated"))
        self._lines.append(f"[bold]Updated:[/bold] {updated}")
        return self

    def add_components(self) -> Self:
        """Add components line if present."""
        components = self._fields.get("components", [])
        if components:
            names = ", ".join([c["name"] for c in components])
            self._lines.append(f"[bold]Components:[/bold] {names}")
        return self

    def add_labels(self) -> Self:
        """Add labels line if present."""
        labels = self._fields.get("labels", [])
        if labels:
            self._lines.append(f"[bold]Labels:[/bold] {', '.join(labels)}")
        return self

    def add_epic_link(self) -> Self:
        """Add epic link line if present."""
        for field_key, field_value in self._fields.items():
            if (
                field_key.startswith("customfield_")
                and isinstance(field_value, str)
                and field_value.upper().startswith("EPIC-")
            ):
                self._lines.append(f"[bold]Epic:[/bold] {field_value}")
                break
        return self

    def add_parent(self) -> Self:
        """Add parent issue link if present."""
        parent = self._fields.get("parent", {})
        if parent:
            self._lines.append(f"[bold]Parent:[/bold] {parent.get('key', 'Unknown')}")
        return self

    def add_epic_name(self) -> Self:
        """Add epic name if this is an epic."""
        epic_name = self._fields.get("customfield_10011")  # Epic Name field
        if epic_name:
            self._lines.append(f"[bold]Epic Name:[/bold] {epic_name}")
        return self

    def add_all_standard(self) -> Self:
        """Add all standard issue fields."""
        return (
            self.add_key()
            .add_summary()
            .add_status()
            .add_priority()
            .add_type()
            .add_assignee()
            .add_reporter()
            .add_created()
            .add_updated()
            .add_components()
            .add_labels()
            .add_epic_link()
        )

    def build(self) -> Panel:
        """Build the Rich Panel."""
        key = self._issue.get("key", "Issue")
        return Panel("\n".join(self._lines), title=f"Jira Issue: {key}", expand=False)

    def build_lines(self) -> list[str]:
        """Return the built lines without wrapping in Panel."""
        return self._lines.copy()

    @classmethod
    def default(cls, issue: dict[str, Any]) -> Panel:
        """Build panel with all standard fields."""
        return cls(issue).add_all_standard().build()


class IssueHeaderBuilder:
    """Builder for creating Rich Table header for single issue display."""

    def __init__(self, issue: dict[str, Any]) -> None:
        """Initialize with issue data."""
        self._issue = issue
        self._fields = issue.get("fields", {})
        self._table = Table(show_header=False, box=None, padding=(0, 1))
        self._table.add_column(style="bold cyan")
        self._table.add_column()

    def add_key(self) -> Self:
        """Add issue key row."""
        self._table.add_row("Key:", self._issue.get("key", "N/A"))
        return self

    def add_type(self) -> Self:
        """Add issue type row."""
        self._table.add_row(
            "Type:", self._fields.get("issuetype", {}).get("name", "Unknown")
        )
        return self

    def add_status(self) -> Self:
        """Add status row."""
        self._table.add_row(
            "Status:", self._fields.get("status", {}).get("name", "Unknown")
        )
        return self

    def add_priority(self) -> Self:
        """Add priority row."""
        self._table.add_row(
            "Priority:", self._fields.get("priority", {}).get("name", "None")
        )
        return self

    def add_reporter(self) -> Self:
        """Add reporter row if present."""
        reporter = self._fields.get("reporter", {})
        if reporter:
            self._table.add_row("Reporter:", reporter.get("displayName", "Unknown"))
        return self

    def add_assignee(self) -> Self:
        """Add assignee row."""
        assignee = self._fields.get("assignee", {})
        if assignee:
            self._table.add_row("Assignee:", assignee.get("displayName", "Unassigned"))
        else:
            self._table.add_row("Assignee:", "Unassigned")
        return self

    def add_created(self) -> Self:
        """Add created date row if present."""
        created = self._fields.get("created")
        if created:
            self._table.add_row("Created:", format_date_relative(created))
        return self

    def add_updated(self) -> Self:
        """Add updated date row if present."""
        updated = self._fields.get("updated")
        if updated:
            self._table.add_row("Updated:", format_date_relative(updated))
        return self

    def add_resolution(self) -> Self:
        """Add resolution row if present."""
        resolution = self._fields.get("resolution")
        if resolution and isinstance(resolution, dict):
            self._table.add_row("Resolution:", resolution.get("name", "Unknown"))
        return self

    def add_components(self) -> Self:
        """Add components row if present."""
        components = self._fields.get("components", [])
        if components:
            names = ", ".join(c.get("name", "") for c in components)
            self._table.add_row("Components:", names)
        return self

    def add_fix_versions(self) -> Self:
        """Add fix versions row if present."""
        fix_versions = self._fields.get("fixVersions", [])
        if fix_versions:
            names = ", ".join(v.get("name", "") for v in fix_versions)
            self._table.add_row("Fix Versions:", names)
        return self

    def add_labels(self) -> Self:
        """Add labels row if present."""
        labels = self._fields.get("labels", [])
        if labels:
            self._table.add_row("Labels:", ", ".join(labels))
        return self

    def add_story_points(self) -> Self:
        """Add story points row if present (customfield_10016)."""
        story_points = self._fields.get("customfield_10016")
        if story_points is not None:
            self._table.add_row("Story Points:", str(story_points))
        return self

    def add_sprint(self) -> Self:
        """Add sprint row if present (customfield_10020)."""
        sprint_data = self._fields.get("customfield_10020")
        if sprint_data:
            if isinstance(sprint_data, list) and sprint_data:
                # Take the last (most recent) sprint
                sprint = sprint_data[-1]
                if isinstance(sprint, dict):
                    name = sprint.get("name", "Unknown")
                    state = sprint.get("state", "")
                    display = f"{name} ({state})" if state else name
                    self._table.add_row("Sprint:", display)
                else:
                    self._table.add_row("Sprint:", str(sprint))
            elif isinstance(sprint_data, dict):
                name = sprint_data.get("name", "Unknown")
                self._table.add_row("Sprint:", name)
        return self

    def add_parent(self) -> Self:
        """Add parent issue row if present."""
        parent = self._fields.get("parent")
        if parent and isinstance(parent, dict):
            key = parent.get("key", "")
            summary = parent.get("fields", {}).get("summary", "")
            display = f"{key} - {summary}" if summary else key
            self._table.add_row("Parent:", display)
        return self

    def _add_option_field(self, field_id: str, label: str) -> Self:
        """Add a custom field that is a single {value: ...} option dict."""
        value = self._fields.get(field_id)
        if value and isinstance(value, dict):
            self._table.add_row(f"{label}:", value.get("value", ""))
        return self

    def _add_option_list_field(self, field_id: str, label: str) -> Self:
        """Add a custom field that is a list of {value: ...} option dicts."""
        values = self._fields.get(field_id)
        if values and isinstance(values, list):
            names = ", ".join(
                v.get("value", "") for v in values if isinstance(v, dict)
            )
            if names:
                self._table.add_row(f"{label}:", names)
        return self

    def add_project_stage(self) -> Self:
        """Add project stage row if present."""
        return self._add_option_field("customfield_10445", "Project Stage")

    def add_phase(self) -> Self:
        """Add phase row if present."""
        return self._add_option_field("customfield_10429", "Phase")

    def add_peer_review_design(self) -> Self:
        """Add peer review design row if present."""
        return self._add_option_field("customfield_10527", "Peer Review - Design")

    def add_peer_review_testing(self) -> Self:
        """Add peer review testing row if present."""
        return self._add_option_field("customfield_10528", "Peer Review - Testing")

    def add_agreement_to_proceed(self) -> Self:
        """Add agreement to proceed row if present."""
        return self._add_option_field("customfield_10530", "Agreement To Proceed")

    def add_design_applicable(self) -> Self:
        """Add design applicable row if present."""
        return self._add_option_field("customfield_10414", "Design Applicable?")

    def add_design_complexity(self) -> Self:
        """Add design complexity row if present."""
        return self._add_option_field("customfield_10428", "Design Complexity")

    def add_on_time(self) -> Self:
        """Add on time RAG status row if present."""
        return self._add_option_field("customfield_10447", "On Time")

    def add_in_budget(self) -> Self:
        """Add in budget RAG status row if present."""
        return self._add_option_field("customfield_10446", "In Budget")

    def add_overall(self) -> Self:
        """Add overall RAG status row if present."""
        return self._add_option_field("customfield_10450", "Overall")

    def add_category(self) -> Self:
        """Add category row if present."""
        return self._add_option_field("customfield_10430", "Category")

    def add_skill_area(self) -> Self:
        """Add skill area row if present."""
        return self._add_option_list_field("customfield_10517", "Skill Area")

    def add_employee_type(self) -> Self:
        """Add employee type row if present."""
        return self._add_option_field("customfield_10343", "Employee Type")

    def add_campaign_name(self) -> Self:
        """Add campaign name row if present."""
        return self._add_option_field("customfield_10436", "Campaign Name")

    def add_status_category_changed(self) -> Self:
        """Add status category changed date row if present."""
        value = self._fields.get("statuscategorychangedate")
        if value:
            self._table.add_row("Status Category Changed:", format_date_relative(value))
        return self

    def add_all_standard(self) -> Self:
        """Add all standard header fields."""
        return (
            self.add_key()
            .add_type()
            .add_status()
            .add_priority()
            .add_resolution()
            .add_reporter()
            .add_assignee()
            .add_created()
            .add_updated()
            .add_components()
            .add_fix_versions()
            .add_labels()
            .add_story_points()
            .add_sprint()
            .add_parent()
            .add_status_category_changed()
            .add_project_stage()
            .add_phase()
            .add_design_applicable()
            .add_design_complexity()
            .add_peer_review_design()
            .add_peer_review_testing()
            .add_agreement_to_proceed()
            .add_on_time()
            .add_in_budget()
            .add_overall()
            .add_category()
            .add_skill_area()
            .add_employee_type()
            .add_campaign_name()
        )

    def build(self) -> Table:
        """Build the Rich Table."""
        return self._table

    def build_panel(self) -> Panel:
        """Build table wrapped in Panel with summary as title."""
        summary = self._fields.get("summary", "No Summary")
        return Panel(self._table, title=f"[bold]{summary}[/bold]")

    @classmethod
    def default(cls, issue: dict[str, Any]) -> Panel:
        """Build header panel with all standard fields."""
        return cls(issue).add_all_standard().build_panel()


def _format_size(size_bytes: int | float) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_issue(
    issue: dict[str, Any],
    comments: list[dict[str, Any]] | None = None,
    show_all_fields: bool = False,
) -> None:
    """Format and display a single Jira issue with rich formatting.

    Args:
        issue: Issue data dict from Jira API
        comments: Optional list of comment dicts to display (from client.get_comments())
        show_all_fields: If True, show unmapped custom fields in "Other Fields" section.
    """
    if not issue or "fields" not in issue:
        console.print("[red]Invalid issue data received[/red]")
        return

    fields = issue.get("fields", {})

    # Display header panel (now includes resolution, components, versions, etc.)
    console.print(IssueHeaderBuilder.default(issue))

    # Display description if available
    description = fields.get("description")
    if description:
        console.print("\n[bold]Description:[/bold]")
        if isinstance(description, dict) and description.get("type") == "doc":
            formatted_text = extract_text_from_adf(description)
            console.print(formatted_text if formatted_text else "(No description content)")
        elif isinstance(description, str):
            console.print(description)

    # Display labels
    labels = fields.get("labels", [])
    if labels:
        console.print(f"\n[bold]Labels:[/bold] {', '.join(labels)}")

    # Display epic details if it's an epic
    epic_name = fields.get("customfield_10011")  # Epic Name field
    if epic_name:
        console.print(f"\n[bold]Epic Name:[/bold] {epic_name}")

    # Display parent/epic link
    parent = fields.get("parent", {})
    if parent:
        console.print(f"\n[bold]Parent:[/bold] {parent.get('key', 'Unknown')}")

    epic_link = fields.get("customfield_10014")  # Epic Link field
    if epic_link:
        console.print(f"\n[bold]Epic Link:[/bold] {epic_link}")

    # ---------------------------------------------------------------------------
    # Subtasks
    # ---------------------------------------------------------------------------
    subtasks = fields.get("subtasks", [])
    if subtasks:
        console.print("\n[bold]Subtasks:[/bold]")
        sub_table = Table(show_header=True, box=None, padding=(0, 1))
        sub_table.add_column("Key", style="cyan")
        sub_table.add_column("Summary")
        sub_table.add_column("Status", style="green")
        for st in subtasks:
            sub_fields = st.get("fields", {})
            sub_table.add_row(
                st.get("key", ""),
                sub_fields.get("summary", ""),
                sub_fields.get("status", {}).get("name", ""),
            )
        console.print(sub_table)

    # ---------------------------------------------------------------------------
    # Linked issues
    # ---------------------------------------------------------------------------
    issue_links = fields.get("issuelinks", [])
    if issue_links:
        console.print("\n[bold]Linked Issues:[/bold]")
        link_table = Table(show_header=True, box=None, padding=(0, 1))
        link_table.add_column("Relation", style="dim")
        link_table.add_column("Key", style="cyan")
        link_table.add_column("Summary")
        link_table.add_column("Status", style="green")
        for link in issue_links:
            link_type = link.get("type", {})
            if "outwardIssue" in link:
                direction = link_type.get("outward", "relates to")
                linked = link["outwardIssue"]
            elif "inwardIssue" in link:
                direction = link_type.get("inward", "is related to")
                linked = link["inwardIssue"]
            else:
                continue
            linked_fields = linked.get("fields", {})
            link_table.add_row(
                direction,
                linked.get("key", ""),
                linked_fields.get("summary", ""),
                linked_fields.get("status", {}).get("name", ""),
            )
        console.print(link_table)

    # ---------------------------------------------------------------------------
    # Attachments
    # ---------------------------------------------------------------------------
    attachments = fields.get("attachment", [])
    if attachments:
        console.print("\n[bold]Attachments:[/bold]")
        att_table = Table(show_header=True, box=None, padding=(0, 1))
        att_table.add_column("Filename", style="cyan")
        att_table.add_column("Size", justify="right")
        for att in attachments:
            size = att.get("size", 0)
            att_table.add_row(
                att.get("filename", "unknown"),
                _format_size(size),
            )
        console.print(att_table)

    # ---------------------------------------------------------------------------
    # Comments — prefer inline comments from fields, fall back to passed-in list
    # ---------------------------------------------------------------------------
    inline_comments = (
        fields.get("comment", {}).get("comments")
        if isinstance(fields.get("comment"), dict)
        else None
    )
    effective_comments = inline_comments or comments
    if effective_comments:
        console.print(f"\n[bold]Comments ({len(effective_comments)}):[/bold]")
        for c in effective_comments:
            author = c.get("author", {}).get("displayName", "Unknown")
            created = format_date(c.get("created"))
            console.print(f"\n  [bold]{author}[/bold] — [dim]{created}[/dim]")
            body = c.get("body")
            if body:
                text = extract_text_from_adf(body) if isinstance(body, dict) else str(body)
                # Indent comment body
                for line in text.split("\n"):
                    console.print(f"  {line}")

    # ---------------------------------------------------------------------------
    # Other Fields — render unmapped custom fields with non-null values
    # Only shown when --fields all is passed
    # ---------------------------------------------------------------------------
    if not show_all_fields:
        return

    known_custom_fields = {
        "customfield_10011",  # Epic Name
        "customfield_10014",  # Epic Link
        "customfield_10016",  # Story Points
        "customfield_10020",  # Sprint
        "customfield_10445",  # Project Stage
        "customfield_10429",  # Phase
        "customfield_10527",  # Peer Review - Design
        "customfield_10528",  # Peer Review - Testing
        "customfield_10530",  # Agreement To Proceed
        "customfield_10414",  # Design Applicable?
        "customfield_10428",  # Design Complexity
        "customfield_10447",  # On Time
        "customfield_10446",  # In Budget
        "customfield_10450",  # Overall
        "customfield_10430",  # Category
        "customfield_10517",  # Skill Area
        "customfield_10343",  # Employee Type
        "customfield_10436",  # Campaign Name
    }
    names_map: dict[str, str] = issue.get("names", {})
    other_fields: list[tuple[str, str]] = []
    for key, value in fields.items():
        if not key.startswith("customfield_"):
            continue
        if key in known_custom_fields:
            continue
        if value is None:
            continue
        # Empty collections / empty strings
        if isinstance(value, (list, dict, str)) and not value:
            continue

        # Render based on type
        rendered: str | None = None
        if isinstance(value, dict):
            if value.get("type") == "doc":
                rendered = extract_text_from_adf(value)
            elif "value" in value:
                rendered = str(value["value"])
        elif isinstance(value, list):
            # List of dicts with "value" key, or list of strings
            parts = []
            for item in value:
                if isinstance(item, dict) and "value" in item:
                    parts.append(str(item["value"]))
                elif isinstance(item, dict) and "name" in item:
                    parts.append(str(item["name"]))
                elif isinstance(item, str):
                    parts.append(item)
            rendered = ", ".join(parts) if parts else None
        elif isinstance(value, str):
            if value.strip().startswith("<"):
                rendered = re.sub(r"<[^>]+>", "", value).strip()
            else:
                rendered = value
        elif isinstance(value, (int, float)):
            rendered = str(value)

        if rendered and rendered.strip():
            label = names_map.get(key, key)
            other_fields.append((label, rendered.strip()))

    if other_fields:
        console.print("\n[bold]Other Fields:[/bold]")
        of_table = Table(show_header=False, box=None, padding=(0, 1))
        of_table.add_column(style="bold cyan")
        of_table.add_column()
        for label, val in other_fields:
            of_table.add_row(f"{label}:", val)
        console.print(of_table)
