"""Tests for composable section functions."""

from jira_tool.document.builders.base import DocumentBuilder
from jira_tool.document.builders.sections import (
    acceptance_criteria_section,
    acceptance_rationale_section,
    description_section,
    done_criteria_section,
    edge_cases_section,
    header_panel,
    implementation_details_section,
    mitigation_section,
    monitoring_plan_section,
    out_of_scope_section,
    problem_statement_section,
    risk_assessment_section,
    steps_section,
    success_metrics_section,
    technical_notes_section,
    testing_considerations_section,
    testing_notes_section,
)


def _build_and_get_content(builder: DocumentBuilder) -> list[dict]:
    """Build ADF and return the content array."""
    adf = builder.build()
    return adf["content"]


class TestHeaderPanel:
    def test_renders_heading_and_panel(self) -> None:
        builder = DocumentBuilder()
        header_panel(builder, "My Title", {"priority": "P1"}, "rocket", "warning")
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert content[0]["attrs"]["level"] == 1
        assert "\U0001f680" in content[0]["content"][0]["text"]  # 🚀
        assert content[1]["type"] == "panel"
        assert content[1]["attrs"]["panelType"] == "warning"

    def test_omits_none_fields(self) -> None:
        builder = DocumentBuilder()
        header_panel(builder, "Title", {}, "clipboard", "info")
        content = _build_and_get_content(builder)
        # Should have heading but no panel (no fields to show)
        assert content[0]["type"] == "heading"
        assert len(content) == 1  # No panel when no fields

    def test_multiple_fields_separated_by_pipe(self) -> None:
        builder = DocumentBuilder()
        header_panel(builder, "T", {"priority": "P1", "services": "API"}, "rocket", "info")
        content = _build_and_get_content(builder)
        panel_para = content[1]["content"][0]  # paragraph inside panel
        texts = [n["text"] for n in panel_para["content"]]
        assert " | " in texts  # separator present


class TestDescriptionSection:
    def test_adds_heading_and_note_panel(self) -> None:
        builder = DocumentBuilder()
        description_section(builder, "Some description")
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert "Description" in content[0]["content"][0]["text"]
        assert content[1]["type"] == "panel"
        assert content[1]["attrs"]["panelType"] == "note"


class TestAcceptanceCriteriaSection:
    def test_adds_heading_and_success_panel_with_ordered_list(self) -> None:
        builder = DocumentBuilder()
        acceptance_criteria_section(builder, ["Criterion 1", "Criterion 2"])
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert "Acceptance Criteria" in content[0]["content"][0]["text"]
        assert content[1]["type"] == "panel"
        assert content[1]["attrs"]["panelType"] == "success"
        assert content[1]["content"][0]["type"] == "orderedList"


class TestRiskAssessmentSection:
    def test_adds_heading_and_warning_panel_with_table(self) -> None:
        builder = DocumentBuilder()
        risk_assessment_section(builder, "Low", "High", "Medium")
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert "Risk Assessment" in content[0]["content"][0]["text"]
        assert content[1]["type"] == "panel"
        assert content[1]["attrs"]["panelType"] == "warning"


class TestImplementationDetailsSection:
    def test_adds_heading_and_info_panel_with_bullet_list(self) -> None:
        builder = DocumentBuilder()
        implementation_details_section(builder, ["Detail 1", "Detail 2"])
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert content[1]["type"] == "panel"
        assert content[1]["attrs"]["panelType"] == "info"
        assert content[1]["content"][0]["type"] == "bulletList"


class TestMitigationSection:
    def test_adds_warning_panel(self) -> None:
        builder = DocumentBuilder()
        mitigation_section(builder, ["Strategy 1"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "warning"


class TestMonitoringPlanSection:
    def test_adds_info_panel_with_ordered_list(self) -> None:
        builder = DocumentBuilder()
        monitoring_plan_section(builder, ["Check weekly"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "info"
        assert content[1]["content"][0]["type"] == "orderedList"


class TestOutOfScopeSection:
    def test_adds_error_panel(self) -> None:
        builder = DocumentBuilder()
        out_of_scope_section(builder, ["Not this"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "error"


class TestStepsSection:
    def test_adds_ordered_list_no_panel(self) -> None:
        builder = DocumentBuilder()
        steps_section(builder, ["Step 1", "Step 2"])
        content = _build_and_get_content(builder)
        assert content[0]["type"] == "heading"
        assert content[1]["type"] == "orderedList"


class TestDoneCriteriaSection:
    def test_adds_success_panel(self) -> None:
        builder = DocumentBuilder()
        done_criteria_section(builder, ["All tests pass"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "success"


class TestProblemStatementSection:
    def test_adds_note_panel(self) -> None:
        builder = DocumentBuilder()
        problem_statement_section(builder, "Users can't log in")
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "note"


class TestEdgeCasesSection:
    def test_adds_note_panel_bullet_list(self) -> None:
        builder = DocumentBuilder()
        edge_cases_section(builder, ["Edge 1"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "note"
        assert content[1]["content"][0]["type"] == "bulletList"


class TestSuccessMetricsSection:
    def test_adds_info_panel(self) -> None:
        builder = DocumentBuilder()
        success_metrics_section(builder, ["Metric 1"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "info"


class TestAcceptanceRationaleSection:
    def test_adds_note_panel_paragraph(self) -> None:
        builder = DocumentBuilder()
        acceptance_rationale_section(builder, "We accept this because...")
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "note"
        assert content[1]["content"][0]["type"] == "paragraph"


class TestTechnicalNotesSection:
    def test_adds_note_panel(self) -> None:
        builder = DocumentBuilder()
        technical_notes_section(builder, ["Note 1"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "note"


class TestTestingNotesSection:
    def test_adds_info_panel(self) -> None:
        builder = DocumentBuilder()
        testing_notes_section(builder, ["Test note"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "info"


class TestTestingConsiderationsSection:
    def test_adds_info_panel_ordered_list(self) -> None:
        builder = DocumentBuilder()
        testing_considerations_section(builder, ["Consider 1"])
        content = _build_and_get_content(builder)
        assert content[1]["attrs"]["panelType"] == "info"
        assert content[1]["content"][0]["type"] == "orderedList"
