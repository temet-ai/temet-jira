"""TypedBuilder — composes ADF documents from type profiles and sections."""

from __future__ import annotations

from typing import Any

from jira_tool.document.builders.base import DocumentBuilder
from jira_tool.document.builders.profiles import get_profile
from jira_tool.document.builders.sections import SECTION_REGISTRY, header_panel


class TypedBuilder(DocumentBuilder):
    """A document builder that composes sections based on a type profile.

    Example:
        builder = TypedBuilder("risk", "CVE Vulnerability",
                               likelihood="Low", impact="High", overall_risk="Medium")
        builder.add_section("description", text="Found CVEs in base image")
        builder.add_section("risk_assessment", likelihood="Low", impact="High", overall="Medium")
        adf = builder.build()
    """

    def __init__(self, issue_type: str, title: str, **kwargs: Any) -> None:
        super().__init__()
        self.issue_type = issue_type
        self.profile = get_profile(issue_type)
        self.title = title
        self.kwargs = kwargs
        self._build_header()

    def _build_header(self) -> None:
        """Build header from profile's emoji, title, and header_fields."""
        emoji = self.profile["emoji"]
        panel_type = self.profile["header_panel_type"]
        fields = {k: self.kwargs.get(k) for k in self.profile["header_fields"]}
        present_fields = {k: v for k, v in fields.items() if v is not None}
        header_panel(self, self.title, present_fields, emoji, panel_type)

    def add_section(self, section_name: str, **kwargs: Any) -> TypedBuilder:
        """Add a section by name. Validates against profile's allowed sections.

        Raises ValueError if section_name is not in the profile's section list.
        """
        if section_name not in self.profile["sections"]:
            raise ValueError(
                f"Section '{section_name}' is not in the '{self.issue_type}' profile. "
                f"Available: {self.profile['sections']}"
            )
        SECTION_REGISTRY[section_name](self, **kwargs)
        return self

    def add_section_optional(self, section_name: str, **kwargs: Any) -> TypedBuilder:
        """Add a section if it's in this type's profile, skip otherwise."""
        if section_name in self.profile["sections"]:
            SECTION_REGISTRY[section_name](self, **kwargs)
        return self
