"""Backward compatibility tests for refactored builders.

Tests structural equivalence: same node types in same order with same text.
Not byte-for-byte ADF JSON identity.
"""

from temet_jira.document.builders.epic import EpicBuilder
from temet_jira.document.builders.issue import IssueBuilder
from temet_jira.document.builders.subtask import SubtaskBuilder
from temet_jira.document.builders.typed import TypedBuilder


def _node_types(adf: dict) -> list[str]:
    """Extract node type sequence from ADF content."""
    return [node["type"] for node in adf["content"]]


def _heading_texts(adf: dict) -> list[str]:
    """Extract heading texts from ADF content."""
    texts = []
    for node in adf["content"]:
        if node["type"] == "heading" and "content" in node:
            texts.append(node["content"][0]["text"])
    return texts


class TestEpicBuilderCompat:
    def test_header_structure(self) -> None:
        epic = EpicBuilder("Auth System", "P1", dependencies="Auth0", services="API")
        adf = epic.build()
        types = _node_types(adf)
        assert types[0] == "heading"  # title
        assert types[1] == "panel"    # info panel
        headings = _heading_texts(adf)
        assert any("\U0001f680" in h for h in headings)  # 🚀 in title

    def test_add_description(self) -> None:
        epic = EpicBuilder("T", "P1").add_description("Desc text")
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Description" in h for h in headings)

    def test_add_acceptance_criteria(self) -> None:
        epic = EpicBuilder("T", "P1").add_acceptance_criteria(["C1", "C2"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Acceptance Criteria" in h for h in headings)

    def test_add_problem_statement(self) -> None:
        epic = EpicBuilder("T", "P1").add_problem_statement("Problem")
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Problem Statement" in h for h in headings)

    def test_add_technical_details(self) -> None:
        epic = EpicBuilder("T", "P1").add_technical_details(["Req 1"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Implementation Details" in h for h in headings)

    def test_add_technical_details_with_code(self) -> None:
        epic = EpicBuilder("T", "P1").add_technical_details(["R"], code_example="x=1")
        adf = epic.build()
        types = _node_types(adf)
        assert "codeBlock" in types

    def test_add_edge_cases(self) -> None:
        epic = EpicBuilder("T", "P1").add_edge_cases(["E1"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Edge Cases" in h for h in headings)

    def test_add_out_of_scope(self) -> None:
        epic = EpicBuilder("T", "P1").add_out_of_scope(["OS1"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Out of Scope" in h for h in headings)

    def test_add_success_metrics(self) -> None:
        epic = EpicBuilder("T", "P1").add_success_metrics(["M1"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Success Metrics" in h for h in headings)

    def test_add_testing_considerations(self) -> None:
        epic = EpicBuilder("T", "P1").add_testing_considerations(["TC1"])
        adf = epic.build()
        headings = _heading_texts(adf)
        assert any("Testing Considerations" in h for h in headings)

    def test_is_typed_builder(self) -> None:
        assert issubclass(EpicBuilder, TypedBuilder)


class TestIssueBuilderCompat:
    def test_header_with_all_fields(self) -> None:
        issue = IssueBuilder("Login Form", "Frontend", story_points=3, epic_key="PROJ-1")
        adf = issue.build()
        types = _node_types(adf)
        assert types[0] == "heading"
        assert types[1] == "panel"
        panel_text = str(adf["content"][1])
        assert "Component" in panel_text
        assert "Story Points" in panel_text
        assert "Epic" in panel_text

    def test_header_omits_none_fields(self) -> None:
        issue = IssueBuilder("Task", "Backend")
        adf = issue.build()
        panel_text = str(adf["content"][1])
        assert "Component" in panel_text
        assert "Story Points" not in panel_text
        assert "Epic" not in panel_text

    def test_epic_key_attribute(self) -> None:
        issue = IssueBuilder("T", "C", epic_key="X-1")
        assert issue.epic_key == "X-1"

    def test_add_description(self) -> None:
        issue = IssueBuilder("T", "C").add_description("Desc")
        headings = _heading_texts(issue.build())
        assert any("Description" in h for h in headings)

    def test_add_implementation_details(self) -> None:
        issue = IssueBuilder("T", "C").add_implementation_details(["D1"])
        headings = _heading_texts(issue.build())
        assert any("Implementation Details" in h for h in headings)

    def test_add_acceptance_criteria(self) -> None:
        issue = IssueBuilder("T", "C").add_acceptance_criteria(["C1"])
        headings = _heading_texts(issue.build())
        assert any("Acceptance Criteria" in h for h in headings)

    def test_add_technical_notes(self) -> None:
        issue = IssueBuilder("T", "C").add_technical_notes(["N1"])
        headings = _heading_texts(issue.build())
        assert any("Technical Notes" in h for h in headings)

    def test_add_testing_notes(self) -> None:
        issue = IssueBuilder("T", "C").add_testing_notes(["TN1"])
        headings = _heading_texts(issue.build())
        assert any("Testing Notes" in h for h in headings)

    def test_add_dependencies(self) -> None:
        issue = IssueBuilder("T", "C").add_dependencies(["D1"])
        headings = _heading_texts(issue.build())
        assert any("Dependencies" in h for h in headings)

    def test_add_code_example(self) -> None:
        issue = IssueBuilder("T", "C").add_code_example("x=1", title="Example")
        types = _node_types(issue.build())
        assert "codeBlock" in types

    def test_is_typed_builder(self) -> None:
        assert issubclass(IssueBuilder, TypedBuilder)


class TestSubtaskBuilderCompat:
    def test_header_with_parent_only(self) -> None:
        st = SubtaskBuilder("Fix bug", parent_key="PROJ-1")
        adf = st.build()
        panel_text = str(adf["content"][1])
        assert "Parent" in panel_text
        assert "Estimate" not in panel_text

    def test_header_with_estimate(self) -> None:
        st = SubtaskBuilder("Fix bug", parent_key="PROJ-1", estimated_hours=4.0)
        adf = st.build()
        panel_text = str(adf["content"][1])
        assert "Parent" in panel_text
        assert "Estimate" in panel_text

    def test_add_description(self) -> None:
        st = SubtaskBuilder("T").add_description("Desc")
        adf = st.build()
        # SubtaskBuilder description is a plain paragraph (no panel)
        assert any(n["type"] == "paragraph" for n in adf["content"][1:])

    def test_add_steps(self) -> None:
        st = SubtaskBuilder("T").add_steps(["S1", "S2"])
        headings = _heading_texts(st.build())
        assert any("Steps" in h for h in headings)

    def test_add_done_criteria(self) -> None:
        st = SubtaskBuilder("T").add_done_criteria(["Done 1"])
        headings = _heading_texts(st.build())
        assert any("Done When" in h for h in headings)

    def test_add_notes(self) -> None:
        st = SubtaskBuilder("T").add_notes(["Note 1"])
        types = _node_types(st.build())
        assert "bulletList" in types

    def test_add_blockers(self) -> None:
        st = SubtaskBuilder("T").add_blockers(["Blocker 1"])
        headings = _heading_texts(st.build())
        assert any("Blockers" in h for h in headings)

    def test_add_code_snippet(self) -> None:
        st = SubtaskBuilder("T").add_code_snippet("x=1")
        types = _node_types(st.build())
        assert "codeBlock" in types

    def test_is_typed_builder(self) -> None:
        assert issubclass(SubtaskBuilder, TypedBuilder)
