"""Composable section functions for ADF document builders.

Each section function appends content to a DocumentBuilder. Sections own their
heading text, emoji, panel type, and content structure. They are composed by
TypedBuilder via type profiles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from temet_jira.document.builders.profiles import EMOJI_MAP, FIELD_LABELS
from temet_jira.document.nodes.block import (
    BulletList,
    Heading,
    OrderedList,
    Panel,
    Paragraph,
    Table,
    TableCell,
    TableHeader,
    TableRow,
)
from temet_jira.document.nodes.inline import Text
from temet_jira.document.nodes.marks import Strong

if TYPE_CHECKING:
    from temet_jira.document.builders.base import DocumentBuilder


def header_panel(
    builder: DocumentBuilder,
    title: str,
    fields: dict[str, str],
    emoji: str,
    panel_type: Literal["info", "note", "warning", "success", "error"],
) -> None:
    """Render a level-1 heading + key-value info panel.

    Args:
        builder: The builder to append to
        title: Heading text (emoji character is prepended)
        fields: Dict of field_name -> value (already filtered for None)
        emoji: Emoji key from EMOJI_MAP (e.g., "rocket")
        panel_type: Panel style ("info", "warning", etc.)
    """
    emoji_char = EMOJI_MAP.get(emoji, emoji)
    builder._content.append(Heading(f"{emoji_char} {title}", level=1))

    if not fields:
        return  # No fields to show — skip the panel

    parts: list[Text] = []
    for i, (key, value) in enumerate(fields.items()):
        if i > 0:
            parts.append(Text(" | "))
        label = FIELD_LABELS.get(key, key.replace("_", " ").title())
        parts.append(Text(f"{label}: ", marks=[Strong()]))
        parts.append(Text(str(value)))

    builder._content.append(Panel(Paragraph(*parts), panel_type=panel_type))


def description_section(builder: DocumentBuilder, text: str) -> None:
    """Add description section with note panel."""
    builder._content.append(Heading("\U0001f4cb Description", level=2))  # 📋
    builder._content.append(Panel(Paragraph(text), panel_type="note"))


def acceptance_criteria_section(builder: DocumentBuilder, criteria: list[str]) -> None:
    """Add acceptance criteria as ordered list in success panel."""
    builder._content.append(Heading("\u2705 Acceptance Criteria", level=2))  # ✅
    builder._content.append(Panel(OrderedList(*criteria), panel_type="success"))


def implementation_details_section(builder: DocumentBuilder, details: list[str]) -> None:
    """Add implementation details as bullet list in info panel."""
    builder._content.append(Heading("\U0001f527 Implementation Details", level=2))  # 🔧
    builder._content.append(Panel(BulletList(*details), panel_type="info"))


def risk_assessment_section(
    builder: DocumentBuilder, likelihood: str, impact: str, overall: str
) -> None:
    """Add risk assessment as table in warning panel."""
    builder._content.append(Heading("\u26a0\ufe0f Risk Assessment", level=2))  # ⚠️

    header = TableRow(
        TableHeader(Paragraph("Dimension")),
        TableHeader(Paragraph("Rating")),
    )
    rows = [
        TableRow(TableCell(Paragraph("Likelihood")), TableCell(Paragraph(likelihood))),
        TableRow(TableCell(Paragraph("Impact")), TableCell(Paragraph(impact))),
        TableRow(TableCell(Paragraph("Overall")), TableCell(Paragraph(overall))),
    ]
    builder._content.append(
        Panel(Table(header, *rows), panel_type="warning")
    )


def mitigation_section(builder: DocumentBuilder, strategies: list[str]) -> None:
    """Add mitigation strategies as bullet list in warning panel."""
    builder._content.append(Heading("\U0001f6e1\ufe0f Mitigation", level=2))  # 🛡️
    builder._content.append(Panel(BulletList(*strategies), panel_type="warning"))


def acceptance_rationale_section(builder: DocumentBuilder, rationale: str) -> None:
    """Add rationale for acceptance as paragraph in note panel."""
    builder._content.append(Heading("\U0001f4cb Rationale for Acceptance", level=2))  # 📋
    builder._content.append(Panel(Paragraph(rationale), panel_type="note"))


def monitoring_plan_section(builder: DocumentBuilder, steps: list[str]) -> None:
    """Add monitoring plan as ordered list in info panel."""
    builder._content.append(Heading("\U0001f4e1 Monitoring Plan", level=2))  # 📡
    builder._content.append(Panel(OrderedList(*steps), panel_type="info"))


def dependencies_section(builder: DocumentBuilder, deps: list[str]) -> None:
    """Add dependencies as bullet list in warning panel."""
    builder._content.append(Heading("\U0001f517 Dependencies", level=2))  # 🔗
    builder._content.append(Panel(BulletList(*deps), panel_type="warning"))


def steps_section(builder: DocumentBuilder, steps: list[str]) -> None:
    """Add implementation steps as ordered list (no panel)."""
    builder._content.append(Heading("\U0001f4dd Steps", level=2))  # 📝
    builder._content.append(OrderedList(*steps))


def done_criteria_section(builder: DocumentBuilder, criteria: list[str]) -> None:
    """Add done criteria as bullet list in success panel."""
    builder._content.append(Heading("\u2705 Done When", level=2))  # ✅
    builder._content.append(Panel(BulletList(*criteria), panel_type="success"))


def technical_notes_section(builder: DocumentBuilder, notes: list[str]) -> None:
    """Add technical notes as bullet list in note panel."""
    builder._content.append(Heading("\U0001f4dd Technical Notes", level=2))  # 📝
    builder._content.append(Panel(BulletList(*notes), panel_type="note"))


def testing_notes_section(builder: DocumentBuilder, notes: list[str]) -> None:
    """Add testing notes as bullet list in info panel."""
    builder._content.append(Heading("\U0001f9ea Testing Notes", level=2))  # 🧪
    builder._content.append(Panel(BulletList(*notes), panel_type="info"))


def out_of_scope_section(builder: DocumentBuilder, items: list[str]) -> None:
    """Add out-of-scope items as bullet list in error panel."""
    builder._content.append(Heading("\U0001f6ab Out of Scope", level=2))  # 🚫
    builder._content.append(Panel(BulletList(*items), panel_type="error"))


def problem_statement_section(builder: DocumentBuilder, problem: str) -> None:
    """Add problem statement as paragraph in note panel."""
    builder._content.append(Heading("\u26a0\ufe0f Problem Statement", level=2))  # ⚠️
    builder._content.append(Panel(Paragraph(problem), panel_type="note"))


def edge_cases_section(builder: DocumentBuilder, cases: list[str]) -> None:
    """Add edge cases as bullet list in note panel."""
    builder._content.append(Heading("\u26a1 Edge Cases", level=2))  # ⚡
    builder._content.append(Panel(BulletList(*cases), panel_type="note"))


def testing_considerations_section(builder: DocumentBuilder, cases: list[str]) -> None:
    """Add testing considerations as ordered list in info panel."""
    builder._content.append(Heading("\U0001f9ea Testing Considerations", level=2))  # 🧪
    builder._content.append(Panel(OrderedList(*cases), panel_type="info"))


def success_metrics_section(builder: DocumentBuilder, metrics: list[str]) -> None:
    """Add success metrics as bullet list in info panel."""
    builder._content.append(Heading("\U0001f4ca Success Metrics", level=2))  # 📊
    builder._content.append(Panel(BulletList(*metrics), panel_type="info"))


# Registry mapping section name -> function
SECTION_REGISTRY: dict[str, Any] = {
    "description": description_section,
    "acceptance_criteria": acceptance_criteria_section,
    "implementation_details": implementation_details_section,
    "risk_assessment": risk_assessment_section,
    "mitigation": mitigation_section,
    "acceptance_rationale": acceptance_rationale_section,
    "monitoring_plan": monitoring_plan_section,
    "dependencies": dependencies_section,
    "steps": steps_section,
    "done_criteria": done_criteria_section,
    "technical_notes": technical_notes_section,
    "testing_notes": testing_notes_section,
    "out_of_scope": out_of_scope_section,
    "problem_statement": problem_statement_section,
    "edge_cases": edge_cases_section,
    "testing_considerations": testing_considerations_section,
    "success_metrics": success_metrics_section,
}
