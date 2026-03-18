"""Tests for TypedBuilder."""

import pytest

from jira_tool.document.builders.typed import TypedBuilder


def _content(builder: TypedBuilder) -> list[dict]:
    return builder.build()["content"]


class TestTypedBuilderInit:
    def test_epic_creates_header_with_rocket_emoji(self) -> None:
        b = TypedBuilder("epic", "Auth System", priority="P1", dependencies="None", services="API")
        content = _content(b)
        assert "\U0001f680" in content[0]["content"][0]["text"]  # 🚀

    def test_risk_creates_header_with_warning_emoji(self) -> None:
        b = TypedBuilder("risk", "CVE Vuln", likelihood="Low", impact="High", overall_risk="Medium")
        content = _content(b)
        assert "\u26a0" in content[0]["content"][0]["text"]  # ⚠️

    def test_unknown_type_uses_default_profile(self) -> None:
        b = TypedBuilder("Unicorn", "Something", component="X")
        content = _content(b)
        assert "\U0001f4cb" in content[0]["content"][0]["text"]  # 📋

    def test_none_header_fields_omitted(self) -> None:
        b = TypedBuilder("sub-task", "Fix bug", parent="PROJ-1")
        content = _content(b)
        # Should have heading + panel with only parent field (no estimated_hours)
        panel_text = str(content[1])
        assert "Parent" in panel_text
        assert "Estimate" not in panel_text

    def test_stores_issue_type(self) -> None:
        b = TypedBuilder("risk", "Title")
        assert b.issue_type == "risk"


class TestAddSection:
    def test_adds_valid_section(self) -> None:
        b = TypedBuilder("risk", "CVE", likelihood="Low", impact="High", overall_risk="Low")
        b.add_section("description", text="A vulnerability exists")
        content = _content(b)
        # Header (heading + panel) + description (heading + panel) = 4 nodes
        assert len(content) == 4

    def test_raises_for_invalid_section(self) -> None:
        b = TypedBuilder("risk", "CVE")
        with pytest.raises(ValueError, match="not in the 'risk' profile"):
            b.add_section("implementation_details", details=["x"])

    def test_add_section_optional_skips_silently(self) -> None:
        b = TypedBuilder("risk", "CVE")
        before = len(b._content)
        b.add_section_optional("implementation_details", details=["x"])
        assert len(b._content) == before  # nothing added

    def test_add_section_optional_adds_when_valid(self) -> None:
        b = TypedBuilder("risk", "CVE")
        b.add_section_optional("description", text="Desc")
        content = _content(b)
        assert any("Description" in str(node) for node in content)


class TestRiskDocument:
    def test_full_risk_document(self) -> None:
        b = TypedBuilder("risk", "CVE in base image",
                         likelihood="Low", impact="High", overall_risk="Low")
        b.add_section("description", text="Vulns in distroless image")
        b.add_section("risk_assessment", likelihood="Low", impact="High", overall="Low")
        b.add_section("mitigation", strategies=["Monitor upstream"])
        b.add_section("acceptance_criteria", criteria=["CVEs resolved"])
        b.add_section("monitoring_plan", steps=["Weekly image check"])
        adf = b.build()
        assert adf["type"] == "doc"
        assert adf["version"] == 1
        # Header(2) + desc(2) + risk(2) + mitigation(2) + AC(2) + monitor(2) = 12
        assert len(adf["content"]) == 12
