"""ADF document builder for Jira Epics."""

from __future__ import annotations

from temet_jira.document.builders.sections import (
    acceptance_criteria_section,
    description_section,
    edge_cases_section,
    implementation_details_section,
    out_of_scope_section,
    problem_statement_section,
    success_metrics_section,
    testing_considerations_section,
)
from temet_jira.document.builders.typed import TypedBuilder
from temet_jira.document.nodes.block import CodeBlock


class EpicBuilder(TypedBuilder):
    """Builder for creating Epic documents with standardized layout.

    Thin wrapper around TypedBuilder("epic", ...) preserving the original API.

    Example:
        epic = (
            EpicBuilder("User Authentication", "P1", dependencies="Auth0 SDK")
            .add_problem_statement("Users cannot securely log in")
            .add_description("Implement OAuth2 authentication flow")
            .add_technical_details(["Integrate Auth0", "Add JWT validation"])
            .add_acceptance_criteria(["User can log in", "Session persists"])
            .build()
        )
    """

    def __init__(
        self,
        title: str,
        priority: str,
        dependencies: str | None = None,
        services: str | None = None,
    ) -> None:
        super().__init__(
            "epic",
            title,
            priority=priority,
            dependencies=dependencies,
            services=services,
        )

    def add_problem_statement(self, problem: str) -> EpicBuilder:
        """Add problem statement section."""
        problem_statement_section(self, problem)
        return self

    def add_description(self, description: str) -> EpicBuilder:
        """Add description section."""
        description_section(self, description)
        return self

    def add_technical_details(
        self,
        requirements: list[str],
        code_example: str | None = None,
        code_language: str = "python",
    ) -> EpicBuilder:
        """Add technical details section with requirements list."""
        implementation_details_section(self, requirements)
        if code_example:
            self._content.append(CodeBlock(code_example, code_language))
        return self

    def add_acceptance_criteria(self, criteria: list[str]) -> EpicBuilder:
        """Add acceptance criteria section."""
        acceptance_criteria_section(self, criteria)
        return self

    def add_edge_cases(self, edge_cases: list[str]) -> EpicBuilder:
        """Add edge cases section."""
        edge_cases_section(self, edge_cases)
        return self

    def add_testing_considerations(self, test_cases: list[str]) -> EpicBuilder:
        """Add testing considerations section."""
        testing_considerations_section(self, test_cases)
        return self

    def add_out_of_scope(self, items: list[str]) -> EpicBuilder:
        """Add out-of-scope section to clarify boundaries."""
        out_of_scope_section(self, items)
        return self

    def add_success_metrics(self, metrics: list[str]) -> EpicBuilder:
        """Add success metrics section."""
        success_metrics_section(self, metrics)
        return self
