# Generic Issue Type Support — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support any Jira issue type (Risk, Decision, Spike, etc.) in the `create` command with composable section-based ADF document builders, replacing the current hardcoded Epic/Task if-else.

**Architecture:** Extract shared section functions from existing builders. Define type profiles (dict of emoji + header fields + sections per type). A `TypedBuilder` class composes sections from profiles. Existing `EpicBuilder`/`IssueBuilder`/`SubtaskBuilder` become thin wrappers for backward compat.

**Tech Stack:** Python 3.11+, Click CLI, Rich tables, Jira REST API v3, pytest

**Spec:** `docs/superpowers/specs/2026-03-18-generic-issue-type-support-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/jira_tool/document/builders/base.py` | Modify | Add `add_titled_section`, `add_header_info_panel` helpers |
| `src/jira_tool/document/builders/profiles.py` | Create | `TYPE_PROFILES`, `FIELD_LABELS`, `EMOJI_MAP`, `get_profile()` |
| `src/jira_tool/document/builders/sections.py` | Create | All reusable section functions |
| `src/jira_tool/document/builders/typed.py` | Create | `TypedBuilder` class |
| `src/jira_tool/document/builders/epic.py` | Rewrite | Thin wrapper extending `TypedBuilder` |
| `src/jira_tool/document/builders/issue.py` | Rewrite | Thin wrapper extending `TypedBuilder` |
| `src/jira_tool/document/builders/subtask.py` | Rewrite | Thin wrapper extending `TypedBuilder` |
| `src/jira_tool/document/builders/__init__.py` | Modify | Export `TypedBuilder`, `get_profile` |
| `src/jira_tool/document/__init__.py` | Modify | Re-export `TypedBuilder`, `get_profile` |
| `src/jira_tool/client.py` | Modify | Update `get_issue_types()` to new API endpoint |
| `src/jira_tool/cli.py` | Modify | Add `types` cmd, update `create` routing |
| `tests/document/test_sections.py` | Create | Unit tests for section functions |
| `tests/document/test_profiles.py` | Create | Tests for profiles and get_profile |
| `tests/document/test_typed_builder.py` | Create | Tests for TypedBuilder |
| `tests/document/test_builder_compat.py` | Create | Backward compat tests for wrappers |
| `tests/cli/test_types_command.py` | Create | CLI types command tests |
| `tests/cli/test_create_refactor.py` | Create | Updated create command tests |

---

### Task 1: Add helper methods to base DocumentBuilder

**Files:**
- Modify: `src/jira_tool/document/builders/base.py:46-213`
- Test: `tests/document/test_sections.py` (created in Task 3)

- [ ] **Step 1: Add `add_titled_section` and `add_header_info_panel` to base.py**

Add after the `add` method (line 205), before `build`:

```python
def add_titled_section(
    self,
    title: str,
    *content: "Node | str",
    panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
) -> "DocumentBuilder":
    """Add a heading followed by a panel — the common section pattern."""
    self._content.append(Heading(title, level=2))
    self._content.append(Panel(*content, panel_type=panel_type))
    return self

def add_header_info_panel(
    self,
    title: str,
    fields: dict[str, str],
    emoji: str = "📋",
    panel_type: Literal["info", "note", "warning", "success", "error"] = "info",
    field_labels: dict[str, str] | None = None,
) -> "DocumentBuilder":
    """Add a level-1 heading with emoji + key-value info panel.

    Args:
        title: The heading text (emoji is prepended)
        fields: Dict of field_name -> value (only non-None fields)
        emoji: Emoji character to prepend to heading
        panel_type: Panel style
        field_labels: Map of field_name -> "emoji Label" display string
    """
    from jira_tool.document.builders.profiles import FIELD_LABELS as DEFAULT_LABELS

    labels = field_labels or DEFAULT_LABELS
    self._content.append(Heading(f"{emoji} {title}", level=1))

    parts: list[Text] = []
    for i, (key, value) in enumerate(fields.items()):
        if i > 0:
            parts.append(Text(" | "))
        label = labels.get(key, key.replace("_", " ").title())
        parts.append(Text(f"{label}: ", marks=[Strong()]))
        parts.append(Text(str(value)))

    if parts:
        self._content.append(Panel(Paragraph(*parts), panel_type=panel_type))
    return self
```

- [ ] **Step 2: Verify existing tests still pass**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All existing tests PASS (we only added methods, nothing changed)

- [ ] **Step 3: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/document/builders/base.py
git commit -m "feat(builders): add add_titled_section and add_header_info_panel helpers to base DocumentBuilder"
```

---

### Task 2: Create profiles module

**Files:**
- Create: `src/jira_tool/document/builders/profiles.py`
- Test: `tests/document/test_profiles.py`

- [ ] **Step 1: Write test for profiles**

Create `tests/document/test_profiles.py`:

```python
"""Tests for type profiles and profile lookup."""

from jira_tool.document.builders.profiles import (
    EMOJI_MAP,
    FIELD_LABELS,
    TYPE_PROFILES,
    get_profile,
)


def test_get_profile_known_type() -> None:
    """Known types return their specific profile."""
    profile = get_profile("epic")
    assert profile["emoji"] == "rocket"
    assert "priority" in profile["header_fields"]
    assert "description" in profile["sections"]


def test_get_profile_risk() -> None:
    """Risk type has risk-specific sections."""
    profile = get_profile("risk")
    assert profile["emoji"] == "warning"
    assert "risk_assessment" in profile["sections"]
    assert "monitoring_plan" in profile["sections"]
    assert profile["header_panel_type"] == "warning"


def test_get_profile_case_insensitive() -> None:
    """Profile lookup is case-insensitive."""
    assert get_profile("Epic") == get_profile("epic")
    assert get_profile("RISK") == get_profile("risk")
    assert get_profile("Sub-Task") == get_profile("sub-task")


def test_get_profile_unknown_returns_default() -> None:
    """Unknown types fall back to _default profile."""
    profile = get_profile("Unicorn")
    assert profile == TYPE_PROFILES["_default"]
    assert profile["emoji"] == "clipboard"


def test_all_profiles_have_required_keys() -> None:
    """Every profile must have emoji, header_fields, header_panel_type, sections."""
    required = {"emoji", "header_fields", "header_panel_type", "sections"}
    for name, profile in TYPE_PROFILES.items():
        missing = required - set(profile.keys())
        assert not missing, f"Profile '{name}' missing keys: {missing}"


def test_emoji_map_covers_all_profiles() -> None:
    """Every emoji string in profiles has a mapping in EMOJI_MAP."""
    for name, profile in TYPE_PROFILES.items():
        emoji_key = profile["emoji"]
        assert emoji_key in EMOJI_MAP, (
            f"Profile '{name}' uses emoji '{emoji_key}' not in EMOJI_MAP"
        )


def test_field_labels_cover_all_header_fields() -> None:
    """Every header field across all profiles has a label."""
    for name, profile in TYPE_PROFILES.items():
        for field in profile["header_fields"]:
            assert field in FIELD_LABELS, (
                f"Profile '{name}' header field '{field}' has no FIELD_LABELS entry"
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_profiles.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'jira_tool.document.builders.profiles'`

- [ ] **Step 3: Create profiles.py**

Create `src/jira_tool/document/builders/profiles.py`:

```python
"""Type profiles for Jira issue types.

Each profile declares which sections a type uses, its header fields,
and display settings. Profiles drive the TypedBuilder.
"""

from typing import Any

# Emoji short names -> Unicode characters
EMOJI_MAP: dict[str, str] = {
    "rocket": "\U0001f680",      # 🚀
    "warning": "\u26a0\ufe0f",   # ⚠️
    "pushpin": "\U0001f4cc",     # 📌
    "clipboard": "\U0001f4cb",   # 📋
}

# Field name -> display label with emoji prefix
FIELD_LABELS: dict[str, str] = {
    "priority": "\u26a0\ufe0f Priority",         # ⚠️ Priority
    "dependencies": "\U0001f517 Dependencies",    # 🔗 Dependencies
    "services": "\u2699\ufe0f Services",          # ⚙️ Services
    "component": "\u2699\ufe0f Component",        # ⚙️ Component
    "story_points": "\U0001f4ca Story Points",    # 📊 Story Points
    "epic": "\U0001f517 Epic",                    # 🔗 Epic
    "parent": "\U0001f517 Parent",                # 🔗 Parent
    "estimated_hours": "\u23f1\ufe0f Estimate",   # ⏱️ Estimate
    "likelihood": "\U0001f4ca Likelihood",        # 📊 Likelihood
    "impact": "\U0001f4a5 Impact",                # 💥 Impact
    "overall_risk": "\u26a0\ufe0f Overall Risk",  # ⚠️ Overall Risk
}

TYPE_PROFILES: dict[str, dict[str, Any]] = {
    "epic": {
        "emoji": "rocket",
        "header_fields": ["priority", "dependencies", "services"],
        "header_panel_type": "warning",
        "sections": [
            "description",
            "problem_statement",
            "acceptance_criteria",
            "implementation_details",
            "edge_cases",
            "testing_considerations",
            "out_of_scope",
            "success_metrics",
        ],
    },
    "risk": {
        "emoji": "warning",
        "header_fields": ["likelihood", "impact", "overall_risk"],
        "header_panel_type": "warning",
        "sections": [
            "description",
            "risk_assessment",
            "mitigation",
            "acceptance_rationale",
            "acceptance_criteria",
            "monitoring_plan",
        ],
    },
    "sub-task": {
        "emoji": "pushpin",
        "header_fields": ["parent", "estimated_hours"],
        "header_panel_type": "info",
        "sections": [
            "description",
            "steps",
            "done_criteria",
        ],
    },
    "_default": {
        "emoji": "clipboard",
        "header_fields": ["component", "story_points", "epic"],
        "header_panel_type": "info",
        "sections": [
            "description",
            "implementation_details",
            "acceptance_criteria",
        ],
    },
}


def get_profile(issue_type: str) -> dict[str, Any]:
    """Get the profile for an issue type, falling back to _default.

    Lookup is case-insensitive.
    """
    return TYPE_PROFILES.get(issue_type.lower(), TYPE_PROFILES["_default"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_profiles.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/document/builders/profiles.py tests/document/test_profiles.py
git commit -m "feat(builders): add type profiles with EMOJI_MAP, FIELD_LABELS, TYPE_PROFILES, get_profile"
```

---

### Task 3: Create sections module

**Files:**
- Create: `src/jira_tool/document/builders/sections.py`
- Test: `tests/document/test_sections.py`

- [ ] **Step 1: Write tests for section functions**

Create `tests/document/test_sections.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_sections.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create sections.py**

Create `src/jira_tool/document/builders/sections.py`:

```python
"""Composable section functions for ADF document builders.

Each section function appends content to a DocumentBuilder. Sections own their
heading text, emoji, panel type, and content structure. They are composed by
TypedBuilder via type profiles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jira_tool.document.builders.profiles import EMOJI_MAP, FIELD_LABELS
from jira_tool.document.nodes.block import (
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
from jira_tool.document.nodes.inline import Text
from jira_tool.document.nodes.marks import Strong

if TYPE_CHECKING:
    from jira_tool.document.builders.base import DocumentBuilder


def header_panel(
    builder: DocumentBuilder,
    title: str,
    fields: dict[str, str],
    emoji: str,
    panel_type: str,
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_sections.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/document/builders/sections.py tests/document/test_sections.py
git commit -m "feat(builders): add composable section functions with SECTION_REGISTRY"
```

---

### Task 4: Create TypedBuilder

**Files:**
- Create: `src/jira_tool/document/builders/typed.py`
- Test: `tests/document/test_typed_builder.py`

- [ ] **Step 1: Write tests for TypedBuilder**

Create `tests/document/test_typed_builder.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_typed_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create typed.py**

Create `src/jira_tool/document/builders/typed.py`:

```python
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

    def add_section(self, section_name: str, **kwargs: Any) -> "TypedBuilder":
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

    def add_section_optional(self, section_name: str, **kwargs: Any) -> "TypedBuilder":
        """Add a section if it's in this type's profile, skip otherwise."""
        if section_name in self.profile["sections"]:
            SECTION_REGISTRY[section_name](self, **kwargs)
        return self
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_typed_builder.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/document/builders/typed.py tests/document/test_typed_builder.py
git commit -m "feat(builders): add TypedBuilder with profile-driven section composition"
```

---

### Task 5: Refactor existing builders to extend TypedBuilder

**Files:**
- Rewrite: `src/jira_tool/document/builders/epic.py`
- Rewrite: `src/jira_tool/document/builders/issue.py`
- Rewrite: `src/jira_tool/document/builders/subtask.py`
- Modify: `src/jira_tool/document/builders/__init__.py`
- Modify: `src/jira_tool/document/__init__.py`
- Test: `tests/document/test_builder_compat.py`

- [ ] **Step 1: Write backward compatibility tests**

Create `tests/document/test_builder_compat.py`:

```python
"""Backward compatibility tests for refactored builders.

Tests structural equivalence: same node types in same order with same text.
Not byte-for-byte ADF JSON identity.
"""

from jira_tool.document.builders.epic import EpicBuilder
from jira_tool.document.builders.issue import IssueBuilder
from jira_tool.document.builders.subtask import SubtaskBuilder
from jira_tool.document.builders.typed import TypedBuilder


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
```

- [ ] **Step 2: Run tests to confirm current builders work (but will fail issubclass checks)**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_builder_compat.py -v`
Expected: Some PASS (structure tests), some FAIL (issubclass TypedBuilder)

- [ ] **Step 3: Rewrite epic.py**

Replace `src/jira_tool/document/builders/epic.py` with:

```python
"""ADF document builder for Jira Epics."""

from __future__ import annotations

from jira_tool.document.builders.sections import (
    acceptance_criteria_section,
    description_section,
    edge_cases_section,
    implementation_details_section,
    out_of_scope_section,
    problem_statement_section,
    success_metrics_section,
    testing_considerations_section,
)
from jira_tool.document.builders.typed import TypedBuilder
from jira_tool.document.nodes.block import CodeBlock


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

    def add_problem_statement(self, problem: str) -> "EpicBuilder":
        """Add problem statement section."""
        problem_statement_section(self, problem)
        return self

    def add_description(self, description: str) -> "EpicBuilder":
        """Add description section."""
        description_section(self, description)
        return self

    def add_technical_details(
        self,
        requirements: list[str],
        code_example: str | None = None,
        code_language: str = "python",
    ) -> "EpicBuilder":
        """Add technical details section with requirements list."""
        implementation_details_section(self, requirements)
        if code_example:
            self._content.append(CodeBlock(code_example, code_language))
        return self

    def add_acceptance_criteria(self, criteria: list[str]) -> "EpicBuilder":
        """Add acceptance criteria section."""
        acceptance_criteria_section(self, criteria)
        return self

    def add_edge_cases(self, edge_cases: list[str]) -> "EpicBuilder":
        """Add edge cases section."""
        edge_cases_section(self, edge_cases)
        return self

    def add_testing_considerations(self, test_cases: list[str]) -> "EpicBuilder":
        """Add testing considerations section."""
        testing_considerations_section(self, test_cases)
        return self

    def add_out_of_scope(self, items: list[str]) -> "EpicBuilder":
        """Add out-of-scope section to clarify boundaries."""
        out_of_scope_section(self, items)
        return self

    def add_success_metrics(self, metrics: list[str]) -> "EpicBuilder":
        """Add success metrics section."""
        success_metrics_section(self, metrics)
        return self
```

- [ ] **Step 4: Rewrite issue.py**

Replace `src/jira_tool/document/builders/issue.py` with:

```python
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
```

- [ ] **Step 5: Rewrite subtask.py**

Replace `src/jira_tool/document/builders/subtask.py` with:

```python
"""ADF document builder for Jira Subtasks."""

from __future__ import annotations

from jira_tool.document.builders.sections import (
    done_criteria_section,
    steps_section,
)
from jira_tool.document.builders.typed import TypedBuilder
from jira_tool.document.nodes.block import BulletList, CodeBlock, Heading, Panel, Paragraph


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

    def add_description(self, description: str) -> "SubtaskBuilder":
        """Add a brief description (plain paragraph, no panel)."""
        self._content.append(Paragraph(description))
        return self

    def add_steps(self, steps: list[str]) -> "SubtaskBuilder":
        """Add implementation steps as an ordered list."""
        steps_section(self, steps)
        return self

    def add_done_criteria(self, criteria: list[str]) -> "SubtaskBuilder":
        """Add definition of done criteria."""
        done_criteria_section(self, criteria)
        return self

    def add_notes(self, notes: list[str]) -> "SubtaskBuilder":
        """Add technical notes."""
        self._content.append(Heading("\U0001f4dd Notes", level=2))  # 📝
        self._content.append(BulletList(*notes))
        return self

    def add_code_snippet(self, code: str, language: str = "python") -> "SubtaskBuilder":
        """Add a code snippet for reference."""
        self._content.append(CodeBlock(code, language))
        return self

    def add_blockers(self, blockers: list[str]) -> "SubtaskBuilder":
        """Add blockers or dependencies."""
        self._content.append(Heading("\U0001f6a7 Blockers", level=2))  # 🚧
        self._content.append(Panel(BulletList(*blockers), panel_type="warning"))
        return self
```

- [ ] **Step 6: Update builders/__init__.py**

Replace `src/jira_tool/document/builders/__init__.py`:

```python
"""ADF document builders for Jira issue types.

Each Jira issue type has its own specialized builder with appropriate
sections and formatting for that type.
"""

from jira_tool.document.builders.base import DocumentBuilder, header_row, row
from jira_tool.document.builders.epic import EpicBuilder
from jira_tool.document.builders.issue import IssueBuilder
from jira_tool.document.builders.profiles import get_profile
from jira_tool.document.builders.subtask import SubtaskBuilder
from jira_tool.document.builders.typed import TypedBuilder

__all__ = [
    # Base builder
    "DocumentBuilder",
    "row",
    "header_row",
    # Typed builder
    "TypedBuilder",
    "get_profile",
    # Issue type builders
    "EpicBuilder",
    "IssueBuilder",
    "SubtaskBuilder",
]
```

- [ ] **Step 7: Update document/__init__.py to re-export TypedBuilder and get_profile**

Add to imports in `src/jira_tool/document/__init__.py`:

In the `from jira_tool.document.builders import (...)` block, add `TypedBuilder` and `get_profile`.

In the `__all__` list, add `"TypedBuilder"` and `"get_profile"` after `"SubtaskBuilder"`.

- [ ] **Step 8: Run backward compat tests**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/document/test_builder_compat.py -v`
Expected: All PASS

- [ ] **Step 9: Run full test suite**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/document/builders/epic.py src/jira_tool/document/builders/issue.py src/jira_tool/document/builders/subtask.py src/jira_tool/document/builders/__init__.py src/jira_tool/document/__init__.py tests/document/test_builder_compat.py
git commit -m "refactor(builders): thin down EpicBuilder, IssueBuilder, SubtaskBuilder to extend TypedBuilder"
```

---

### Task 6: Update client.get_issue_types to new API endpoint

**Files:**
- Modify: `src/jira_tool/client.py:502-521`
- Test: `tests/test_client.py` (add new test)

- [ ] **Step 1: Write test for updated get_issue_types**

Add to `tests/test_client.py`:

```python
def test_get_issue_types_new_endpoint(jira_client, mock_response):
    """Test get_issue_types uses new createmeta endpoint."""
    mock_response.json.return_value = {
        "issueTypes": [
            {"id": "1", "name": "Task", "subtask": False},
            {"id": "2", "name": "Risk", "subtask": False},
        ]
    }
    with patch.object(jira_client.session, "request", return_value=mock_response):
        types = jira_client.get_issue_types("PROJ")
        assert len(types) == 2
        assert types[0]["name"] == "Task"
        assert types[1]["name"] == "Risk"


def test_get_issue_types_fallback(jira_client, mock_response):
    """Test get_issue_types falls back to old endpoint on 404."""
    from requests.exceptions import HTTPError

    new_response = MagicMock()
    new_response.raise_for_status.side_effect = HTTPError(response=MagicMock(status_code=404))

    old_response = MagicMock()
    old_response.json.return_value = {
        "projects": [{"issuetypes": [{"name": "Bug", "subtask": False}]}]
    }
    old_response.raise_for_status = MagicMock()

    with patch.object(
        jira_client.session, "request", side_effect=[new_response, old_response]
    ):
        types = jira_client.get_issue_types("PROJ")
        assert len(types) == 1
        assert types[0]["name"] == "Bug"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/test_client.py -k "test_get_issue_types" -v`
Expected: FAIL

- [ ] **Step 3: Update get_issue_types in client.py**

Replace `get_issue_types` method (lines 502-521) in `src/jira_tool/client.py`:

```python
def get_issue_types(self, project_key: str) -> list[dict[str, Any]]:
    """Get available issue types for a project.

    Uses the new createmeta/{project}/issuetypes endpoint first,
    falls back to the deprecated createmeta endpoint if unavailable.

    Args:
        project_key: Project key

    Returns:
        List of issue types
    """
    # Try new endpoint first
    try:
        url = f"{self.base_url}/rest/api/3/issue/createmeta/{project_key}/issuetypes"
        response = self._request("GET", url)
        data = cast(dict[str, Any], response.json())
        return cast(list[dict[str, Any]], data.get("issueTypes", data.get("values", [])))
    except requests.exceptions.HTTPError:
        pass

    # Fallback to deprecated endpoint
    url = f"{self.base_url}/rest/api/3/issue/createmeta"
    params = {"projectKeys": project_key, "expand": "projects.issuetypes.fields"}

    response = self._request("GET", url, params=params)
    data = cast(dict[str, Any], response.json())

    projects = data.get("projects")
    if projects and isinstance(projects, list) and len(projects) > 0:
        project = cast(dict[str, Any], projects[0])
        return cast(list[dict[str, Any]], project.get("issuetypes", []))
    return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/test_client.py -k "test_get_issue_types" -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/client.py tests/test_client.py
git commit -m "feat(client): update get_issue_types to new createmeta API with fallback"
```

---

### Task 7: Add `types` CLI command and update `create` command

**Files:**
- Modify: `src/jira_tool/cli.py:30,496-597`
- Test: `tests/cli/test_types_command.py`
- Test: `tests/cli/test_create_refactor.py`

- [ ] **Step 1: Write tests for types command**

Create `tests/cli/test_types_command.py`:

```python
"""Tests for jira-tool types command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from jira_tool.cli import jira


@patch("jira_tool.cli.JiraClient")
def test_types_command_displays_table(mock_client_cls):
    """types command shows issue types in a table."""
    mock_client = MagicMock()
    mock_client.get_issue_types.return_value = [
        {"name": "Task", "subtask": False},
        {"name": "Risk", "subtask": False},
        {"name": "Sub-task", "subtask": True},
    ]
    mock_client_cls.return_value = mock_client

    runner = CliRunner()
    result = runner.invoke(jira, ["types", "--project", "PROJ"])
    assert result.exit_code == 0
    assert "Task" in result.output
    assert "Risk" in result.output
    assert "Sub-task" in result.output


@patch("jira_tool.cli.JiraClient")
def test_types_command_default_project(mock_client_cls):
    """types command uses JIRA_DEFAULT_PROJECT."""
    mock_client = MagicMock()
    mock_client.get_issue_types.return_value = [{"name": "Bug", "subtask": False}]
    mock_client_cls.return_value = mock_client

    runner = CliRunner(env={"JIRA_DEFAULT_PROJECT": "MYPROJ"})
    result = runner.invoke(jira, ["types"])
    assert result.exit_code == 0
    mock_client.get_issue_types.assert_called_once_with("MYPROJ")
```

- [ ] **Step 2: Write tests for updated create command**

Create `tests/cli/test_create_refactor.py`:

```python
"""Tests for updated create command with TypedBuilder."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from jira_tool.cli import jira


@patch("jira_tool.cli.JiraClient")
def test_create_risk_type(mock_client_cls):
    """create --type Risk uses TypedBuilder."""
    mock_client = MagicMock()
    mock_client.create_issue.return_value = {"key": "PROJ-999"}
    mock_client.get_issue.return_value = {
        "key": "PROJ-999",
        "fields": {"summary": "Test Risk", "issuetype": {"name": "Risk"},
                    "status": {"name": "New"}, "priority": {"name": "Medium"}},
    }
    mock_client_cls.return_value = mock_client

    runner = CliRunner()
    result = runner.invoke(jira, [
        "create", "-s", "Test Risk", "--type", "Risk", "--project", "PROJ",
    ])
    assert result.exit_code == 0
    assert "PROJ-999" in result.output

    # Verify issuetype was set correctly
    call_args = mock_client.create_issue.call_args
    fields = call_args[0][0]
    assert fields["issuetype"]["name"] == "Risk"


@patch("jira_tool.cli.JiraClient")
def test_create_help_text_updated(mock_client_cls):
    """create --help shows updated type description."""
    runner = CliRunner()
    result = runner.invoke(jira, ["create", "--help"])
    assert "jira-tool types" in result.output
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/cli/test_types_command.py tests/cli/test_create_refactor.py -v`
Expected: FAIL — types command not found

- [ ] **Step 4: Update cli.py imports**

At the top of `src/jira_tool/cli.py`, add to the `from .document import ...` line (line 30):

Replace the import with only what's needed (EpicBuilder and IssueBuilder are no longer used in cli.py):
```python
from .document import DocumentBuilder, TypedBuilder
```

- [ ] **Step 5: Add `types` command to cli.py**

Add before the `create` command (before line 496):

```python
@jira.command()
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
def types(project: str) -> None:
    """List available issue types for a project."""
    try:
        client = JiraClient()

        with console.status(f"Fetching issue types for {project}..."):
            issue_types = client.get_issue_types(project)

        if not issue_types:
            console.print(f"[yellow]No issue types found for project {project}[/yellow]")
            return

        from jira_tool.document.builders.profiles import TYPE_PROFILES

        from rich.table import Table

        table = Table(title=f"Issue Types — {project}")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Subtask", style="yellow")
        table.add_column("Custom Profile", style="green")

        for it in sorted(issue_types, key=lambda x: x.get("name", "")):
            name = it.get("name", "Unknown")
            subtask = "Yes" if it.get("subtask", False) else "No"
            has_profile = "Yes" if name.lower() in TYPE_PROFILES else "No"
            table.add_row(name, subtask, has_profile)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e
```

- [ ] **Step 6: Update `create` command**

Replace the create command (lines 496-597) in `src/jira_tool/cli.py`. Key changes:
- `--type` help text updated
- Uses `TypedBuilder` for all types
- Special handling only for epic link custom field

```python
@jira.command()
@click.option("--summary", "-s", required=True, help="Issue summary/title")
@click.option("--description", "-d", help="Issue description")
@click.option(
    "--type",
    "-t",
    "issue_type",
    default="Task",
    help="Issue type — run 'jira-tool types' to see available types",
)
@click.option("--epic", "-e", help="Epic key to link to (e.g., PROJ-123)")
@click.option("--priority", "-p", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option(
    "--project",
    default=lambda: os.environ.get("JIRA_DEFAULT_PROJECT", "PROJ"),
    help="Project key (configurable via JIRA_DEFAULT_PROJECT)",
)
def create(
    summary: str,
    description: str | None,
    issue_type: str,
    epic: str | None,
    priority: str | None,
    labels: str | None,
    project: str,
) -> None:
    """Create a new issue in Jira with professional formatting."""
    try:
        client = JiraClient()

        # Parse labels if provided
        label_list = [label.strip() for label in labels.split(",")] if labels else None

        # Build ADF description using TypedBuilder
        # Pass only description — header fields are optional from CLI.
        # For richer documents, use the programmatic API or --description-adf.
        builder = TypedBuilder(issue_type, summary)
        if description:
            builder.add_section_optional("description", text=description)

        fields: dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": builder.build(),
        }

        # Add priority if provided
        if priority:
            fields["priority"] = {"name": priority}

        # Add labels if provided
        if label_list:
            fields["labels"] = label_list

        # Add epic link if provided and not an epic
        if epic and issue_type.lower() != "epic":
            fields["customfield_10014"] = epic  # Epic Link field

        with console.status(f"Creating {issue_type.lower()} in project {project}..."):
            result = client.create_issue(fields)

        issue_key = result.get("key")
        console.print(
            f"[green]\u2713[/green] {issue_type} created successfully: {issue_key}"
        )

        # Show the created issue
        if issue_key:
            issue = client.get_issue(issue_key)
            format_issue(issue)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort() from e
```

- [ ] **Step 7: Run CLI tests**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/cli/test_types_command.py tests/cli/test_create_refactor.py -v`
Expected: All PASS

- [ ] **Step 8: Run full test suite**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
cd /Users/dawiddutoit/projects/ai/tools/jira-tool
git add src/jira_tool/cli.py tests/cli/test_types_command.py tests/cli/test_create_refactor.py
git commit -m "feat(cli): add types command, update create to use TypedBuilder for any issue type"
```

---

### Task 8: Rebuild and manual verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite one final time**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Run linter**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 3: Rebuild and install**

Run: `cd /Users/dawiddutoit/projects/ai/tools/jira-tool && uv build && uv tool install . --force --refresh-package jira-tool`
Expected: Successful install

- [ ] **Step 4: Test types command with real Jira**

Run: `jira-tool types PROJ`
Expected: Table showing all 21 issue types with Risk marked as having custom profile

- [ ] **Step 5: Test get on risk item**

Run: `jira-tool get PROJ-629`
Expected: Same output as before (no regression)

- [ ] **Step 6: Commit if any fixes were needed**

Only if manual testing revealed issues that needed fixing.
