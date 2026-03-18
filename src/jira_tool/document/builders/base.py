"""Base fluent document builder for ADF documents."""

from typing import Any, Literal

from jira_tool.document.nodes.base import Node
from jira_tool.document.nodes.block import (
    Blockquote,
    BulletList,
    CodeBlock,
    Document,
    Expand,
    Heading,
    ListItem,
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
    Mark,
    Strike,
    Strong,
    Subsup,
    TextColor,
    Underline,
)


class DocumentBuilder:
    """Fluent builder for creating ADF documents.

    This is the base class for all Jira issue type builders.
    Use specialized builders (EpicBuilder, IssueBuilder, SubtaskBuilder)
    for issue-type-specific formatting.

    Example (method chaining):
        doc = (
            DocumentBuilder()
            .heading("Title", level=1)
            .paragraph("Some text")
            .bullet_list(["Item 1", "Item 2"])
            .build()
        )

    Example (node construction):
        doc = Document(
            Heading("Title", level=1),
            Paragraph(Text("Some "), Text("text", marks=[Strong()])),
        ).to_adf()
    """

    def __init__(self) -> None:
        self._content: list[Node] = []

    def heading(self, text: str, level: int = 1) -> "DocumentBuilder":
        """Add a heading."""
        self._content.append(Heading(text, level=level))
        return self

    def paragraph(self, *content: Node | str) -> "DocumentBuilder":
        """Add a paragraph with mixed content."""
        self._content.append(Paragraph(*content))
        return self

    def text(self, text: str, marks: list[Mark] | None = None) -> Text:
        """Create a text node (does not add to document)."""
        return Text(text, marks)

    def bold(self, text: str) -> Text:
        """Create bold text node."""
        return Text(text, [Strong()])

    def italic(self, text: str) -> Text:
        """Create italic text node."""
        return Text(text, [Em()])

    def code_inline(self, text: str) -> Text:
        """Create inline code text node."""
        return Text(text, [Code()])

    def strikethrough(self, text: str) -> Text:
        """Create strikethrough text node."""
        return Text(text, [Strike()])

    def underline(self, text: str) -> Text:
        """Create underlined text node."""
        return Text(text, [Underline()])

    def link(self, text: str, href: str, title: str | None = None) -> Text:
        """Create a hyperlink text node."""
        return Text(text, [Link(href, title)])

    def colored(self, text: str, color: str) -> Text:
        """Create colored text node."""
        return Text(text, [TextColor(color)])

    def highlighted(self, text: str, color: str) -> Text:
        """Create highlighted (background color) text node."""
        return Text(text, [BackgroundColor(color)])

    def subscript(self, text: str) -> Text:
        """Create subscript text node."""
        return Text(text, [Subsup("sub")])

    def superscript(self, text: str) -> Text:
        """Create superscript text node."""
        return Text(text, [Subsup("sup")])

    def code_block(self, code: str, language: str = "text") -> "DocumentBuilder":
        """Add a code block."""
        self._content.append(CodeBlock(code, language))
        return self

    def blockquote(self, *content: Node | str) -> "DocumentBuilder":
        """Add a blockquote."""
        self._content.append(Blockquote(*content))
        return self

    def rule(self) -> "DocumentBuilder":
        """Add a horizontal rule."""
        self._content.append(Rule())
        return self

    def panel(
        self,
        *content: Node | str,
        panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
    ) -> "DocumentBuilder":
        """Add a panel (info, note, warning, success, error)."""
        self._content.append(
            Panel(*content, panel_type=panel_type)
        )
        return self

    def bullet_list(self, items: list[str | ListItem]) -> "DocumentBuilder":
        """Add a bullet list."""
        self._content.append(BulletList(*items))
        return self

    def ordered_list(
        self, items: list[str | ListItem], start: int = 1
    ) -> "DocumentBuilder":
        """Add an ordered list."""
        self._content.append(OrderedList(*items, start=start))
        return self

    def expand(self, *content: Node | str, title: str = "") -> "DocumentBuilder":
        """Add an expandable section."""
        self._content.append(Expand(*content, title=title))
        return self

    def table(self, *rows: TableRow) -> "DocumentBuilder":
        """Add a table."""
        self._content.append(Table(*rows))
        return self

    def emoji(self, short_name: str, text: str | None = None) -> Emoji:
        """Create an emoji node (does not add to document)."""
        return Emoji(short_name, text=text)

    def mention(self, account_id: str, display_text: str) -> Mention:
        """Create a mention node (does not add to document)."""
        return Mention(account_id, display_text)

    def date(self, timestamp: str) -> Date:
        """Create a date node (does not add to document)."""
        return Date(timestamp)

    def status(
        self,
        text: str,
        color: Literal["neutral", "purple", "blue", "red", "yellow", "green"] = "neutral",
    ) -> Status:
        """Create a status lozenge node (does not add to document)."""
        return Status(text, color)

    def inline_card(self, url: str) -> InlineCard:
        """Create an inline card/smart link node (does not add to document)."""
        return InlineCard(url)

    def hard_break(self) -> HardBreak:
        """Create a hard break node (does not add to document)."""
        return HardBreak()

    def add(self, node: Node) -> "DocumentBuilder":
        """Add any node to the document."""
        self._content.append(node)
        return self

    def add_titled_section(
        self,
        title: str,
        *content: "Node | str",
        panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
    ) -> "DocumentBuilder":
        """Add a heading followed by a panel — the common section pattern."""
        self._content.append(Heading(title, level=2))
        self._content.append(Panel(*content, panel_type=panel_type))
        return self

    def add_header_info_panel(
        self,
        title: str,
        fields: dict[str, str],
        emoji: str = "\U0001f4cb",
        panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
        field_labels: dict[str, str] | None = None,
    ) -> "DocumentBuilder":
        """Add a level-1 heading with emoji + key-value info panel.

        Args:
            title: The heading text (emoji is prepended)
            fields: Dict of field_name -> value (only non-None fields)
            emoji: Emoji character to prepend to heading
            panel_type: Panel style
            field_labels: Map of field_name -> "emoji Label" display string
        """
        from jira_tool.document.builders.profiles import FIELD_LABELS as DEFAULT_LABELS

        labels = field_labels or DEFAULT_LABELS
        self._content.append(Heading(f"{emoji} {title}", level=1))

        parts: list[Text] = []
        for i, (key, value) in enumerate(fields.items()):
            if i > 0:
                parts.append(Text(" | "))
            label = labels.get(key, key.replace("_", " ").title())
            parts.append(Text(f"{label}: ", marks=[Strong()]))
            parts.append(Text(str(value)))

        if parts:
            self._content.append(Panel(Paragraph(*parts), panel_type=panel_type))
        return self

    def build(self) -> dict[str, Any]:
        """Build the final ADF document."""
        return Document(*self._content).to_adf()

    def build_simple(self, text: str) -> dict[str, Any]:
        """Build a simple single-paragraph document."""
        return Document(Paragraph(text)).to_adf()


def row(*cells: str | Node) -> TableRow:
    """Create a table row from cells."""
    table_cells = [
        (
            cell
            if isinstance(cell, (TableCell, TableHeader))
            else TableCell(Paragraph(cell))
        )
        for cell in cells
    ]
    return TableRow(*table_cells)


def header_row(*cells: str | Node) -> TableRow:
    """Create a table header row."""
    header_cells = [
        cell if isinstance(cell, TableHeader) else TableHeader(Paragraph(cell))
        for cell in cells
    ]
    return TableRow(*header_cells)
