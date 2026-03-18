"""ADF document builder for Jira Subtasks."""

from __future__ import annotations

from jira_tool.document.builders.sections import (
    done_criteria_section,
    steps_section,
)
from jira_tool.document.builders.typed import TypedBuilder
from jira_tool.document.nodes.block import (
    BulletList,
    CodeBlock,
    Heading,
    Panel,
    Paragraph,
)


class SubtaskBuilder(TypedBuilder):
    """Builder for creating Subtask documents with streamlined layout.

    Thin wrapper around TypedBuilder("sub-task", ...) preserving the original API.

    Example:
        subtask = (
            SubtaskBuilder("Validate email format", parent_key="PROJ-456")
            .add_description("Add email validation using regex")
            .add_steps(["Add validation function", "Write unit tests"])
            .add_done_criteria(["All tests pass", "Code reviewed"])
            .build()
        )
    """

    def __init__(
        self,
        title: str,
        parent_key: str | None = None,
        estimated_hours: float | None = None,
    ) -> None:
        super().__init__(
            "sub-task",
            title,
            parent=parent_key,
            estimated_hours=estimated_hours,
        )
        self.estimated_hours = estimated_hours

    def add_description(self, description: str) -> SubtaskBuilder:
        """Add a brief description (plain paragraph, no panel)."""
        self._content.append(Paragraph(description))
        return self

    def add_steps(self, steps: list[str]) -> SubtaskBuilder:
        """Add implementation steps as an ordered list."""
        steps_section(self, steps)
        return self

    def add_done_criteria(self, criteria: list[str]) -> SubtaskBuilder:
        """Add definition of done criteria."""
        done_criteria_section(self, criteria)
        return self

    def add_notes(self, notes: list[str]) -> SubtaskBuilder:
        """Add technical notes."""
        self._content.append(Heading("\U0001f4dd Notes", level=2))  # 📝
        self._content.append(BulletList(*notes))
        return self

    def add_code_snippet(self, code: str, language: str = "python") -> SubtaskBuilder:
        """Add a code snippet for reference."""
        self._content.append(CodeBlock(code, language))
        return self

    def add_blockers(self, blockers: list[str]) -> SubtaskBuilder:
        """Add blockers or dependencies."""
        self._content.append(Heading("\U0001f6a7 Blockers", level=2))  # 🚧
        self._content.append(Panel(BulletList(*blockers), panel_type="warning"))
        return self
