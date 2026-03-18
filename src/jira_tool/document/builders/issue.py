"""ADF document builder for Jira Issues (Tasks/Stories)."""

from __future__ import annotations

from jira_tool.document.builders.sections import (
    acceptance_criteria_section,
    dependencies_section,
    description_section,
    implementation_details_section,
    technical_notes_section,
    testing_notes_section,
)
from jira_tool.document.builders.typed import TypedBuilder
from jira_tool.document.nodes.block import CodeBlock, Heading


class IssueBuilder(TypedBuilder):
    """Builder for creating Issue/Task documents with standardized layout.

    Thin wrapper around TypedBuilder("_default", ...) preserving the original API.
    None values for story_points/epic_key are omitted from the header panel
    (no more "TBD"/"None" sentinels).

    Example:
        issue = (
            IssueBuilder("Add login form", "Frontend", story_points=3)
            .add_description("Create a responsive login form component")
            .add_implementation_details(["Use React Hook Form", "Add validation"])
            .add_acceptance_criteria(["Form validates email", "Shows errors"])
            .build()
        )
    """

    def __init__(
        self,
        title: str,
        component: str,
        story_points: int | None = None,
        epic_key: str | None = None,
    ) -> None:
        # Translate public param names to profile field names
        super().__init__(
            "_default",
            title,
            component=component,
            story_points=story_points,
            epic=epic_key,
        )
        self.epic_key = epic_key  # preserve for backward compat attribute access

    def add_description(self, description: str) -> "IssueBuilder":
        """Add description section in a note panel."""
        description_section(self, description)
        return self

    def add_implementation_details(self, details: list[str]) -> "IssueBuilder":
        """Add implementation details section in an info panel."""
        implementation_details_section(self, details)
        return self

    def add_acceptance_criteria(self, criteria: list[str]) -> "IssueBuilder":
        """Add acceptance criteria section in a success panel."""
        acceptance_criteria_section(self, criteria)
        return self

    def add_technical_notes(self, notes: list[str]) -> "IssueBuilder":
        """Add technical notes section."""
        technical_notes_section(self, notes)
        return self

    def add_code_example(
        self, code: str, language: str = "python", title: str | None = None
    ) -> "IssueBuilder":
        """Add a code example with optional title."""
        if title:
            self._content.append(Heading(f"\U0001f4bb {title}", level=3))  # 💻
        self._content.append(CodeBlock(code, language))
        return self

    def add_dependencies(self, dependencies: list[str]) -> "IssueBuilder":
        """Add dependencies section (blocked by or blocks)."""
        dependencies_section(self, dependencies)
        return self

    def add_testing_notes(self, notes: list[str]) -> "IssueBuilder":
        """Add testing notes section."""
        testing_notes_section(self, notes)
        return self
