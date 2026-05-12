"""ADF block node types."""

from typing import Any, Literal

from temet_jira.document.nodes.base import BlockNode, Node


class Document(BlockNode):
    """Root document node."""

    def __init__(self, *children: Node | str) -> None:
        self.children = children

    @property
    def type(self) -> str:
        return "doc"

    def to_adf(self) -> dict[str, Any]:
        return {
            "version": 1,
            "type": self.type,
            "content": self._build_content(self.children),
        }


class Paragraph(BlockNode):
    """Paragraph node containing inline content."""

    def __init__(self, *children: Node | str) -> None:
        self.children = children

    @property
    def type(self) -> str:
        return "paragraph"

    def to_adf(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type}
        if self.children:
            result["content"] = self._build_content(self.children)
        return result


class Heading(BlockNode):
    """Heading node (h1-h6)."""

    def __init__(self, *children: Node | str, level: int = 1) -> None:
        if not 1 <= level <= 6:
            raise ValueError("Heading level must be between 1 and 6")
        self.children = children
        self.level = level

    @property
    def type(self) -> str:
        return "heading"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {"level": self.level},
            "content": self._build_content(self.children),
        }


class CodeBlock(BlockNode):
    """Code block with syntax highlighting."""

    def __init__(self, code: str, language: str = "text") -> None:
        self.code = code
        self.language = language

    @property
    def type(self) -> str:
        return "codeBlock"

    def to_adf(self) -> dict[str, Any]:
        from temet_jira.document.nodes.inline import Text

        return {
            "type": self.type,
            "attrs": {"language": self.language},
            "content": [Text(self.code).to_adf()],
        }


class Blockquote(BlockNode):
    """Blockquote node for quoted content."""

    def __init__(self, *children: Node | str) -> None:
        self.children = children

    @property
    def type(self) -> str:
        return "blockquote"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self._build_content(self.children),
        }


class Rule(BlockNode):
    """Horizontal rule/divider."""

    @property
    def type(self) -> str:
        return "rule"

    def to_adf(self) -> dict[str, Any]:
        return {"type": self.type}


class Panel(BlockNode):
    """Panel node for highlighted content."""

    VALID_TYPES = ("info", "note", "warning", "success", "error")

    def __init__(
        self,
        *children: Node | str,
        panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
    ) -> None:
        if panel_type not in self.VALID_TYPES:
            raise ValueError(
                f"Panel type must be one of: {', '.join(self.VALID_TYPES)}"
            )
        self.children = children
        self.panel_type = panel_type

    @property
    def type(self) -> str:
        return "panel"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {"panelType": self.panel_type},
            "content": self._build_content(self.children),
        }


class ListItem(BlockNode):
    """List item node."""

    def __init__(self, *children: Node | str) -> None:
        self.children = children

    @property
    def type(self) -> str:
        return "listItem"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self._build_content(self.children),
        }


class BulletList(BlockNode):
    """Unordered/bullet list."""

    def __init__(self, *items: ListItem | str) -> None:
        self.items = items

    @property
    def type(self) -> str:
        return "bulletList"

    def to_adf(self) -> dict[str, Any]:
        content: list[dict[str, Any]] = []
        for item in self.items:
            if isinstance(item, ListItem):
                content.append(item.to_adf())
            elif isinstance(item, str):
                # Auto-wrap strings in ListItem with Paragraph
                content.append(ListItem(Paragraph(item)).to_adf())
        return {"type": self.type, "content": content}


class OrderedList(BlockNode):
    """Ordered/numbered list."""

    def __init__(self, *items: ListItem | str, start: int = 1) -> None:
        self.items = items
        self.start = start

    @property
    def type(self) -> str:
        return "orderedList"

    def to_adf(self) -> dict[str, Any]:
        content: list[dict[str, Any]] = []
        for item in self.items:
            if isinstance(item, ListItem):
                content.append(item.to_adf())
            elif isinstance(item, str):
                content.append(ListItem(Paragraph(item)).to_adf())
        return {
            "type": self.type,
            "attrs": {"order": self.start},
            "content": content,
        }


class Expand(BlockNode):
    """Expandable/collapsible section."""

    def __init__(self, *children: Node | str, title: str = "") -> None:
        self.children = children
        self.title = title

    @property
    def type(self) -> str:
        return "expand"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {"title": self.title},
            "content": self._build_content(self.children),
        }


class NestedExpand(BlockNode):
    """Nested expandable section (for use inside tables, etc.)."""

    def __init__(self, *children: Node | str, title: str = "") -> None:
        self.children = children
        self.title = title

    @property
    def type(self) -> str:
        return "nestedExpand"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {"title": self.title},
            "content": self._build_content(self.children),
        }


# Table nodes
class TableCell(BlockNode):
    """Table cell node."""

    def __init__(
        self,
        *children: Node | str,
        colspan: int = 1,
        rowspan: int = 1,
        col_width: list[int] | None = None,
        background: str | None = None,
    ) -> None:
        self.children = children
        self.colspan = colspan
        self.rowspan = rowspan
        self.col_width = col_width
        self.background = background

    @property
    def type(self) -> str:
        return "tableCell"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self.colspan != 1:
            attrs["colspan"] = self.colspan
        if self.rowspan != 1:
            attrs["rowspan"] = self.rowspan
        if self.col_width:
            attrs["colwidth"] = self.col_width
        if self.background:
            attrs["background"] = self.background

        result: dict[str, Any] = {"type": self.type}
        if attrs:
            result["attrs"] = attrs
        result["content"] = self._build_content(self.children)
        return result


class TableHeader(BlockNode):
    """Table header cell node."""

    def __init__(
        self,
        *children: Node | str,
        colspan: int = 1,
        rowspan: int = 1,
        col_width: list[int] | None = None,
        background: str | None = None,
    ) -> None:
        self.children = children
        self.colspan = colspan
        self.rowspan = rowspan
        self.col_width = col_width
        self.background = background

    @property
    def type(self) -> str:
        return "tableHeader"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self.colspan != 1:
            attrs["colspan"] = self.colspan
        if self.rowspan != 1:
            attrs["rowspan"] = self.rowspan
        if self.col_width:
            attrs["colwidth"] = self.col_width
        if self.background:
            attrs["background"] = self.background

        result: dict[str, Any] = {"type": self.type}
        if attrs:
            result["attrs"] = attrs
        result["content"] = self._build_content(self.children)
        return result


class TableRow(BlockNode):
    """Table row node."""

    def __init__(self, *cells: TableCell | TableHeader) -> None:
        self.cells = cells

    @property
    def type(self) -> str:
        return "tableRow"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": [cell.to_adf() for cell in self.cells],
        }


class Table(BlockNode):
    """Table node."""

    def __init__(
        self,
        *rows: TableRow,
        is_number_column_enabled: bool = False,
        layout: Literal["default", "wide", "full-width"] = "default",
    ) -> None:
        self.rows = rows
        self.is_number_column_enabled = is_number_column_enabled
        self.layout = layout

    @property
    def type(self) -> str:
        return "table"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {
                "isNumberColumnEnabled": self.is_number_column_enabled,
                "layout": self.layout,
            },
            "content": [row.to_adf() for row in self.rows],
        }


# Media nodes
class Media(BlockNode):
    """Media node for images/files."""

    def __init__(
        self,
        media_id: str,
        type_attr: Literal["file", "link", "external"] = "file",
        collection: str = "",
        width: int | None = None,
        height: int | None = None,
        occurrence_key: str | None = None,
        alt: str | None = None,
    ) -> None:
        self.media_id = media_id
        self.type_attr = type_attr
        self.collection = collection
        self.width = width
        self.height = height
        self.occurrence_key = occurrence_key
        self.alt = alt

    @property
    def type(self) -> str:
        return "media"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "id": self.media_id,
            "type": self.type_attr,
            "collection": self.collection,
        }
        if self.width:
            attrs["width"] = self.width
        if self.height:
            attrs["height"] = self.height
        if self.occurrence_key:
            attrs["occurrenceKey"] = self.occurrence_key
        if self.alt:
            attrs["alt"] = self.alt

        return {"type": self.type, "attrs": attrs}


class MediaSingle(BlockNode):
    """Single media item with layout options."""

    def __init__(
        self,
        media: Media,
        layout: Literal[
            "wrap-left",
            "center",
            "wrap-right",
            "wide",
            "full-width",
            "align-start",
            "align-end",
        ] = "center",
        width: float | None = None,
    ) -> None:
        self.media = media
        self.layout = layout
        self.width_percent = width

    @property
    def type(self) -> str:
        return "mediaSingle"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"layout": self.layout}
        if self.width_percent:
            attrs["width"] = self.width_percent

        return {
            "type": self.type,
            "attrs": attrs,
            "content": [self.media.to_adf()],
        }


class MediaGroup(BlockNode):
    """Group of media items."""

    def __init__(self, *media: Media) -> None:
        self.media = media

    @property
    def type(self) -> str:
        return "mediaGroup"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": [m.to_adf() for m in self.media],
        }
