"""Extract plain text from Atlassian Document Format (ADF) content."""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def extract_text_from_adf(content: str | dict[str, Any]) -> str:
    """Extract plain text from ADF content.

    Args:
        content: ADF document dict or plain string

    Returns:
        Plain text representation of the content
    """
    if isinstance(content, str):
        return content

    if not isinstance(content, dict) or content.get("type") != "doc":
        return str(content)

    text_parts: list[str] = []

    for node in content.get("content", []):
        _extract_node(node, text_parts, indent=0)

    return "".join(text_parts).strip()


def _extract_node(node: dict[str, Any], text_parts: list[str], indent: int = 0) -> None:
    """Recursively extract text from an ADF node.

    Priority: known handler → recurse content → direct text → attrs fallback.
    Guarantees no text is silently dropped.
    """
    node_type = node.get("type", "")

    handler = _NODE_HANDLERS.get(node_type)
    if handler:
        handler(node, text_parts, indent)
    elif "content" in node:
        # Unknown node with children — recurse to extract all nested text
        _handle_generic_content(node, text_parts, indent)
    elif "text" in node:
        # Unknown node with a direct text field — treat it like a text node
        text_parts.append(node["text"])
    else:
        # Leaf node with no content and no text — try attrs
        _handle_unknown_leaf(node, text_parts)


# ---------------------------------------------------------------------------
# Existing handlers
# ---------------------------------------------------------------------------


def _handle_text(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle text node."""
    text_parts.append(node.get("text", ""))


def _handle_paragraph(node: dict[str, Any], text_parts: list[str], indent: int) -> None:
    """Handle paragraph node."""
    if text_parts and text_parts[-1] != "\n":
        text_parts.append("\n")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)
    text_parts.append("\n")


def _handle_heading(node: dict[str, Any], text_parts: list[str], indent: int) -> None:
    """Handle heading node."""
    level = node.get("attrs", {}).get("level", 1)
    if text_parts and text_parts[-1] != "\n":
        text_parts.append("\n")
    text_parts.append("#" * level + " ")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)
    text_parts.append("\n")


def _handle_bullet_list(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle bullet list node."""
    for item in node.get("content", []):
        _handle_list_item(item, text_parts, indent, bullet="•")


def _handle_ordered_list(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle ordered list node."""
    start = node.get("attrs", {}).get("order", 1)
    for i, item in enumerate(node.get("content", []), start):
        _handle_list_item(item, text_parts, indent, bullet=f"{i}.")


def _handle_list_item(
    item: dict[str, Any], text_parts: list[str], indent: int, bullet: str
) -> None:
    """Handle a single list item.

    Recursively extracts all children (paragraphs, inline nodes, nested lists)
    instead of only pulling direct text children.
    """
    # Collect inline content from the first paragraph-level child
    item_text: list[str] = []
    children = item.get("content", [])

    for child in children:
        if child.get("type") in ("bulletList", "orderedList"):
            # Nested lists: flush current text first, then recurse deeper
            if item_text or not text_parts or text_parts[-1] != "\n":
                text_parts.append(
                    "  " * indent + f"{bullet} " + "".join(item_text) + "\n"
                )
                item_text = []
            _extract_node(child, text_parts, indent + 1)
        else:
            # Recurse into the child to capture all inline content
            _extract_node(child, item_text, indent)

    # Strip surrounding newlines that paragraph handler may have added
    content = "".join(item_text).strip()
    text_parts.append("  " * indent + f"{bullet} " + content + "\n")


def _handle_code_block(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle code block node."""
    lang = node.get("attrs", {}).get("language", "")
    text_parts.append(f"\n```{lang}\n")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)
    text_parts.append("\n```\n")


def _handle_panel(node: dict[str, Any], text_parts: list[str], indent: int) -> None:
    """Handle panel node."""
    panel_type = node.get("attrs", {}).get("panelType", "info").upper()
    text_parts.append(f"\n[{panel_type}]\n")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)
    text_parts.append("\n")


def _handle_emoji(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle emoji node."""
    attrs = node.get("attrs", {})
    text_parts.append(attrs.get("text", attrs.get("shortName", "")))


# ---------------------------------------------------------------------------
# New inline node handlers
# ---------------------------------------------------------------------------


def _handle_hard_break(
    node: dict[str, Any],  # noqa: ARG001
    text_parts: list[str],
    indent: int,  # noqa: ARG001
) -> None:
    """Handle hardBreak node — line break within a paragraph."""
    text_parts.append("\n")


def _handle_mention(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle mention node (e.g. @John Doe)."""
    attrs = node.get("attrs", {})
    name = attrs.get("text", "")
    if name:
        text_parts.append(name if name.startswith("@") else f"@{name}")
    else:
        text_parts.append("@unknown")


def _handle_date(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle date node — attrs.timestamp is millis since epoch."""
    attrs = node.get("attrs", {})
    timestamp = attrs.get("timestamp")
    if timestamp is not None:
        try:
            ts = int(timestamp) / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            text_parts.append(dt.strftime("%Y-%m-%d"))
        except (ValueError, TypeError, OSError):
            text_parts.append(str(timestamp))
    else:
        text_parts.append("(no date)")


def _handle_status(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle status lozenge node — e.g. [IN PROGRESS]."""
    attrs = node.get("attrs", {})
    text = attrs.get("text", "")
    text_parts.append(f"[{text}]" if text else "[status]")


def _handle_inline_card(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle inlineCard node — renders as a URL."""
    attrs = node.get("attrs", {})
    url = attrs.get("url", "")
    text_parts.append(url if url else "(link)")


# ---------------------------------------------------------------------------
# New block node handlers
# ---------------------------------------------------------------------------


def _handle_blockquote(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle blockquote — prefix child content with '> '."""
    inner: list[str] = []
    for child in node.get("content", []):
        _extract_node(child, inner, indent)
    quoted = "".join(inner).strip()
    for line in quoted.split("\n"):
        text_parts.append(f"> {line}\n")


def _handle_rule(
    node: dict[str, Any],  # noqa: ARG001
    text_parts: list[str],
    indent: int,  # noqa: ARG001
) -> None:
    """Handle horizontal rule node."""
    text_parts.append("\n---\n")


def _handle_expand(node: dict[str, Any], text_parts: list[str], indent: int) -> None:
    """Handle expand / nestedExpand — show title then recurse children."""
    attrs = node.get("attrs", {})
    title = attrs.get("title", "")
    if title:
        text_parts.append(f"[{title}]\n")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


def _handle_table(node: dict[str, Any], text_parts: list[str], indent: int) -> None:
    """Handle table node — rows separated by pipes."""
    for row in node.get("content", []):
        if row.get("type") != "tableRow":
            continue
        cells: list[str] = []
        for cell in row.get("content", []):
            cell_parts: list[str] = []
            for child in cell.get("content", []):
                _extract_node(child, cell_parts, indent)
            cells.append("".join(cell_parts).strip())
        text_parts.append("| " + " | ".join(cells) + " |\n")


def _handle_media(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle mediaSingle / mediaGroup — image or attachment placeholder."""
    for child in node.get("content", []):
        if child.get("type") == "media":
            attrs = child.get("attrs", {})
            alt = attrs.get("alt", "")
            if alt:
                text_parts.append(f"[image: {alt}]")
            else:
                text_parts.append("[attachment]")
            return
    text_parts.append("[attachment]")


# ---------------------------------------------------------------------------
# Remaining ADF spec handlers
# ---------------------------------------------------------------------------


def _handle_list_item_standalone(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle listItem when encountered outside a list context."""
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


def _handle_media_node(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle standalone media node — image or attachment."""
    attrs = node.get("attrs", {})
    alt = attrs.get("alt", "")
    if alt:
        text_parts.append(f"[image: {alt}]")
    else:
        text_parts.append("[attachment]")


def _handle_media_inline(
    node: dict[str, Any], text_parts: list[str], indent: int  # noqa: ARG001
) -> None:
    """Handle inline media reference — show filename or attachment placeholder."""
    attrs = node.get("attrs", {})
    alt = attrs.get("alt", "")
    if alt:
        text_parts.append(f"[{alt}]")
    else:
        text_parts.append("[attachment]")


def _handle_table_row(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle tableRow when encountered outside a table context."""
    cells: list[str] = []
    for cell in node.get("content", []):
        cell_parts: list[str] = []
        for child in cell.get("content", []):
            _extract_node(child, cell_parts, indent)
        cells.append("".join(cell_parts).strip())
    text_parts.append("| " + " | ".join(cells) + " |\n")


def _handle_table_cell(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle tableCell — recurse content."""
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


def _handle_table_header(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle tableHeader — recurse content."""
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


def _handle_multi_bodied_extension(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle multiBodiedExtension macro container."""
    attrs = node.get("attrs", {})
    key = attrs.get("extensionKey", "")
    if key:
        text_parts.append(f"[{key}]\n")
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


def _handle_extension_frame(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle extensionFrame inside multiBodiedExtension — recurse content."""
    for child in node.get("content", []):
        _extract_node(child, text_parts, indent)


# ---------------------------------------------------------------------------
# Fallback handlers
# ---------------------------------------------------------------------------


def _handle_unknown_leaf(node: dict[str, Any], text_parts: list[str]) -> None:
    """Handle unknown leaf nodes (no content key, no text key, no handler).

    Tries in order: node text → attrs.text → attrs.shortName → attrs.url.
    Logs a debug warning if nothing is found.
    """
    # Direct text on the node (same field used by "text" type nodes)
    direct_text = node.get("text")
    if direct_text:
        text_parts.append(str(direct_text))
        return

    attrs = node.get("attrs", {})
    text = attrs.get("text") or attrs.get("shortName") or attrs.get("url")
    if text:
        text_parts.append(str(text))
    else:
        logger.debug(
            "Unknown leaf node type '%s' with no extractable text: %s",
            node.get("type", ""),
            node,
        )


def _handle_generic_content(
    node: dict[str, Any], text_parts: list[str], indent: int
) -> None:
    """Handle nodes with generic content."""
    for child in node["content"]:
        _extract_node(child, text_parts, indent)


# Node type to handler mapping
_NODE_HANDLERS: dict[str, Any] = {
    # Existing
    "text": _handle_text,
    "paragraph": _handle_paragraph,
    "heading": _handle_heading,
    "bulletList": _handle_bullet_list,
    "orderedList": _handle_ordered_list,
    "codeBlock": _handle_code_block,
    "panel": _handle_panel,
    "emoji": _handle_emoji,
    # New inline handlers
    "hardBreak": _handle_hard_break,
    "mention": _handle_mention,
    "date": _handle_date,
    "status": _handle_status,
    "inlineCard": _handle_inline_card,
    # New block handlers
    "blockquote": _handle_blockquote,
    "rule": _handle_rule,
    "expand": _handle_expand,
    "nestedExpand": _handle_expand,
    "table": _handle_table,
    "mediaSingle": _handle_media,
    "mediaGroup": _handle_media,
    # Remaining ADF spec handlers
    "listItem": _handle_list_item_standalone,
    "media": _handle_media_node,
    "mediaInline": _handle_media_inline,
    "tableRow": _handle_table_row,
    "tableCell": _handle_table_cell,
    "tableHeader": _handle_table_header,
    "multiBodiedExtension": _handle_multi_bodied_extension,
    "extensionFrame": _handle_extension_frame,
}
