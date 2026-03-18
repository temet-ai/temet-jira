"""Atlassian Document Format (ADF) document building and display module.

This module provides:
- Type-safe, fluent API for building ADF documents (Jira Cloud REST API v3)
- ADF text extraction for parsing existing documents
- Rich terminal display formatters for Jira data

Example (building ADF):
    from jira_tool.document import Document, Paragraph, Text, Heading
    from jira_tool.document.marks import Strong, Link

    doc = Document(
        Heading("Welcome", level=1),
        Paragraph(
            Text("Hello "),
            Text("world", marks=[Strong(), Link(href="https://example.com")]),
        ),
    )
    adf = doc.to_adf()

Example (extracting text from ADF):
    from jira_tool.document.adf import extract_text_from_adf
    text = extract_text_from_adf(adf_content)

Example (terminal display):
    from jira_tool.document.display import format_issue, IssuePanelBuilder
    format_issue(issue)  # Print to console
    panel = IssuePanelBuilder(issue).add_all_standard().build()
"""

from jira_tool.document.adf import extract_text_from_adf
from jira_tool.document.builders import (
    DocumentBuilder,
    EpicBuilder,
    IssueBuilder,
    SubtaskBuilder,
    TypedBuilder,
    get_profile,
    header_row,
    row,
)
from jira_tool.document.display import (
    IssuePanelBuilder,
    IssueTableBuilder,
    ProjectTableBuilder,
    TransitionTableBuilder,
    format_date,
    format_date_relative,
    format_issue,
    format_issues_table,
    format_projects_table,
    format_transitions_table,
    get_priority,
    get_user_display,
    truncate_summary,
)
from jira_tool.document.nodes.base import Mark, Node
from jira_tool.document.nodes.block import (
    Blockquote,
    BulletList,
    CodeBlock,
    Document,
    Expand,
    Heading,
    ListItem,
    Media,
    MediaGroup,
    MediaSingle,
    NestedExpand,
    OrderedList,
    Panel,
    Paragraph,
    Rule,
    Table,
    TableCell,
    TableHeader,
    TableRow,
)
from jira_tool.document.nodes.inline import (
    Date,
    Emoji,
    HardBreak,
    InlineCard,
    Mention,
    Status,
    Text,
)
from jira_tool.document.nodes.marks import (
    BackgroundColor,
    Code,
    Em,
    Link,
    Strike,
    Strong,
    Subsup,
    TextColor,
    Underline,
)

__all__ = [
    # ADF Builders
    "DocumentBuilder",
    "EpicBuilder",
    "IssueBuilder",
    "SubtaskBuilder",
    "TypedBuilder",
    "get_profile",
    "row",
    "header_row",
    # ADF Extraction
    "extract_text_from_adf",
    # Display Functions
    "format_issue",
    "format_issues_table",
    "format_projects_table",
    "format_transitions_table",
    # Display Formatters
    "format_date",
    "format_date_relative",
    "get_priority",
    "get_user_display",
    "truncate_summary",
    # Display Builders
    "IssuePanelBuilder",
    "IssueTableBuilder",
    "ProjectTableBuilder",
    "TransitionTableBuilder",
    # Base
    "Node",
    "Mark",
    # Block nodes
    "Blockquote",
    "BulletList",
    "CodeBlock",
    "Document",
    "Expand",
    "Heading",
    "ListItem",
    "Media",
    "MediaGroup",
    "MediaSingle",
    "NestedExpand",
    "OrderedList",
    "Panel",
    "Paragraph",
    "Rule",
    "Table",
    "TableCell",
    "TableHeader",
    "TableRow",
    # Inline nodes
    "Date",
    "Emoji",
    "HardBreak",
    "InlineCard",
    "Mention",
    "Status",
    "Text",
    # Marks
    "BackgroundColor",
    "Code",
    "Em",
    "Link",
    "Strike",
    "Strong",
    "Subsup",
    "TextColor",
    "Underline",
]
