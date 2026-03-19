# Generic Issue Type Support — Design Spec

## Problem

The jira-tool `create` command hardcodes support for three issue types (Task, Story, Bug) with
a special path for Epics. The WPCW project alone has 21 issue types including Risk, Decision,
Dependency, Policy, Spike, and more. The current builder architecture duplicates common patterns
across `EpicBuilder`, `IssueBuilder`, and `SubtaskBuilder`, making it expensive to add new types.

## Goals

1. **Any Jira issue type works** with `create` — validated against the project's actual types
2. **Composable section architecture** — shared sections written once, assembled per type via profiles
3. **DRY builders** — extract duplicated patterns from existing builders into reusable sections
4. **Risk type first-class support** — with risk-specific sections (assessment, mitigation, monitoring)
5. **`types` command** — discover available issue types from the Jira API

## Non-Goals

- Interactive form/wizard for creating issues (keep CLI flag-based)
- Auto-generating ADF from Jira field metadata
- Template system with user-defined YAML configs

## Architecture

### Composable Sections

Sections are standalone functions that append content to a `DocumentBuilder`. Each handles
one logical block of an issue description (heading + content in a panel).

Each section function **hard-codes its own panel type** — this is intentional. The panel type
is part of the section's visual identity (acceptance criteria are always green/success,
warnings are always yellow/warning, etc.) and should not be configurable per call.

```
sections.py — each section owns its heading, panel type, and emoji

  header_panel(builder, title, fields: dict[str, str], emoji, panel_type)
      # See "Header Panel Output Contract" below for exact rendering spec

  description_section(builder, text)                          # panel_type="note"
  acceptance_criteria_section(builder, criteria: list[str])   # panel_type="success", OrderedList
  implementation_details_section(builder, details: list[str]) # panel_type="info", BulletList
  risk_assessment_section(builder, likelihood, impact, overall) # panel_type="warning", Table
  mitigation_section(builder, strategies: list[str])          # panel_type="warning", BulletList
  acceptance_rationale_section(builder, rationale: str)        # panel_type="note", Paragraph
  monitoring_plan_section(builder, steps: list[str])          # panel_type="info", OrderedList
  dependencies_section(builder, deps: list[str])              # panel_type="warning", BulletList
  steps_section(builder, steps: list[str])                    # panel_type="info", OrderedList
  done_criteria_section(builder, criteria: list[str])         # panel_type="success", BulletList
  technical_notes_section(builder, notes: list[str])          # panel_type="note", BulletList
  testing_notes_section(builder, notes: list[str])            # panel_type="info", BulletList
  out_of_scope_section(builder, items: list[str])             # panel_type="error", BulletList
  problem_statement_section(builder, problem: str)            # panel_type="note", Paragraph
  edge_cases_section(builder, cases: list[str])               # panel_type="note", BulletList
  testing_considerations_section(builder, cases: list[str])   # panel_type="info", OrderedList
  success_metrics_section(builder, metrics: list[str])        # panel_type="info", BulletList
```

### Header Panel Output Contract

`header_panel` renders the same ADF structure the existing builders produce:

1. **Heading (level 1):** `"{emoji_char} {title}"` — emoji is embedded in the string, not an ADF Emoji node.
   The `emoji` profile field maps to a character: `"rocket" -> "🚀"`, `"warning" -> "⚠️"`, etc.

2. **Panel** of type `panel_type` containing a **single Paragraph** with alternating bold-key / value pairs
   separated by `" | "`:

   ```
   Paragraph(
       Text("⚠️ {Label1}: ", marks=[Strong()]),
       Text("{value1}"),
       Text(" | "),
       Text("🔗 {Label2}: ", marks=[Strong()]),
       Text("{value2}"),
       ...
   )
   ```

3. **Field labels** include their own emoji prefix. The label rendering is defined per profile field:

   ```python
   FIELD_LABELS = {
       "priority": "⚠️ Priority",
       "dependencies": "🔗 Dependencies",
       "services": "⚙️ Services",
       "component": "⚙️ Component",
       "story_points": "📊 Story Points",
       "epic": "🔗 Epic",
       "parent": "🔗 Parent",
       "estimated_hours": "⏱️ Estimate",
       "likelihood": "📊 Likelihood",
       "impact": "💥 Impact",
       "overall_risk": "⚠️ Overall Risk",
   }
   ```

4. **Optional fields:** If a header field value is `None`, that field is **omitted entirely**
   from the panel (no label, no separator). This preserves existing SubtaskBuilder behavior
   where `estimated_hours=None` produces no estimate line.

   Implementation: filter out `None` values before building the Paragraph:
   ```python
   fields = {k: kwargs.get(k) for k in profile["header_fields"]}
   present_fields = {k: v for k, v in fields.items() if v is not None}
   ```

**Backward compatibility test:** The test checks **structural equivalence** — same node types
in same order with same text content — not byte-for-byte ADF JSON identity. Whitespace and
key ordering in the dict may differ.

### Type Profiles

A profile declares which sections a type uses, its header fields, and display settings.

All header fields support `None` values — `None` means the field is omitted from the header panel
entirely. This is how optional fields work (e.g., `estimated_hours` on sub-tasks).

```python
TYPE_PROFILES = {
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
```

Lookup: `TYPE_PROFILES.get(issue_type.lower(), TYPE_PROFILES["_default"])`

### TypedBuilder

A single builder class that composes sections from a profile:

```python
class TypedBuilder(DocumentBuilder):
    def __init__(self, issue_type: str, title: str, **kwargs):
        super().__init__()
        self.issue_type = issue_type
        self.profile = get_profile(issue_type)
        self.title = title
        self.kwargs = kwargs
        self._build_header()

    def _build_header(self):
        """Build header from profile's emoji, title, and header_fields.

        Fields with None values are omitted entirely from the panel.
        """
        emoji = self.profile["emoji"]
        panel_type = self.profile["header_panel_type"]
        # Only include fields that were provided (not None)
        fields = {k: self.kwargs.get(k) for k in self.profile["header_fields"]}
        present_fields = {k: v for k, v in fields.items() if v is not None}
        header_panel(self, self.title, present_fields, emoji, panel_type)

    def add_section(self, section_name: str, **kwargs) -> "TypedBuilder":
        """Add a section by name. Validates against profile's allowed sections.

        Raises ValueError if section_name is not in the profile's section list.
        This catches typos early rather than silently producing incomplete documents.
        Use add_section_optional() for cases where silent skip is desired.
        """
        if section_name not in self.profile["sections"]:
            raise ValueError(
                f"Section '{section_name}' is not in the '{self.issue_type}' profile. "
                f"Available: {self.profile['sections']}"
            )
        SECTION_REGISTRY[section_name](self, **kwargs)
        return self

    def add_section_optional(self, section_name: str, **kwargs) -> "TypedBuilder":
        """Add a section if it's in this type's profile, skip otherwise.

        Use this for generic code that builds documents across multiple types
        where not all sections apply.
        """
        if section_name in self.profile["sections"]:
            SECTION_REGISTRY[section_name](self, **kwargs)
        return self
```

### Base DocumentBuilder Changes

Add shared helper methods used by sections:

```python
# base.py additions

def add_titled_section(self, title: str, *content, panel_type="info"):
    """Heading + panel — the pattern every section uses."""
    self._content.append(Heading(title, level=2))
    self._content.append(Panel(*content, panel_type=panel_type))
    return self

def add_header_info_panel(self, title: str, fields: dict[str, str],
                          emoji: str = "clipboard", panel_type="info"):
    """Title heading with emoji + key-value info panel."""
    # Renders: ## {emoji} {title}
    # Then an info panel with Key: Value pairs
```

### Existing Builders — Thinned Down

`EpicBuilder`, `IssueBuilder`, `SubtaskBuilder` become thin convenience wrappers around
`TypedBuilder`. They keep their current API (method names, constructor signatures) for
backward compatibility but delegate to sections internally.

**All existing public methods are preserved.** Each method delegates to its corresponding
section function. Methods that have no matching section function (because they are unique to
that builder) call the underlying `DocumentBuilder` primitives directly — this is expected
and acceptable since those methods are builder-specific by definition.

```python
class EpicBuilder(TypedBuilder):
    """Convenience wrapper — preserves existing API."""
    def __init__(self, title, priority, dependencies=None, services=None):
        super().__init__("epic", title,
                         priority=priority, dependencies=dependencies, services=services)

    # Methods that delegate to shared sections:
    def add_description(self, description: str) -> "EpicBuilder":
        description_section(self, description)
        return self

    def add_problem_statement(self, problem: str) -> "EpicBuilder":
        problem_statement_section(self, problem)
        return self

    def add_acceptance_criteria(self, criteria: list[str]) -> "EpicBuilder":
        acceptance_criteria_section(self, criteria)
        return self

    def add_technical_details(self, requirements, code_example=None, code_language="python"):
        implementation_details_section(self, requirements)
        if code_example:
            self._content.append(CodeBlock(code_example, code_language))
        return self

    # Methods unique to EpicBuilder — use DocumentBuilder primitives directly:
    def add_edge_cases(self, cases: list[str]) -> "EpicBuilder":
        edge_cases_section(self, cases)
        return self

    def add_testing_considerations(self, cases: list[str]) -> "EpicBuilder":
        testing_considerations_section(self, cases)
        return self

    def add_out_of_scope(self, items: list[str]) -> "EpicBuilder":
        out_of_scope_section(self, items)
        return self

    def add_success_metrics(self, metrics: list[str]) -> "EpicBuilder":
        success_metrics_section(self, metrics)
        return self
```

```python
class IssueBuilder(TypedBuilder):
    """Convenience wrapper — preserves existing API.

    Note: constructor translates `epic_key` -> `epic` for the profile's header_fields.

    Sentinel values: The old IssueBuilder rendered "TBD" for story_points=None and
    "None" for epic_key=None in the header panel. This behavior is INTENTIONALLY DROPPED.
    Under the new architecture, None values are omitted from the header panel (same as
    SubtaskBuilder's estimated_hours). This is a minor visual change — the header panel
    shows fewer fields when values aren't provided, which is cleaner. The backward
    compatibility test for IssueBuilder must verify the NEW behavior (omitted fields),
    not the old sentinel strings.
    """
    def __init__(self, title, component, story_points=None, epic_key=None):
        # Translate public param name to profile field name
        # None values are omitted from header (no more "TBD"/"None" sentinels)
        super().__init__("_default", title,
                         component=component, story_points=story_points, epic=epic_key)
        self.epic_key = epic_key  # preserve for backward compat attribute access

    # ... methods delegate to section functions same as EpicBuilder
```

```python
class SubtaskBuilder(TypedBuilder):
    """Convenience wrapper — preserves existing API.

    Note: estimated_hours=None results in that field being omitted from the header panel.
    """
    def __init__(self, title, parent_key=None, estimated_hours=None):
        super().__init__("sub-task", title,
                         parent=parent_key, estimated_hours=estimated_hours)
    # ... methods delegate to section functions
```

**Kwarg name translation rule:** Wrapper `__init__` methods map their public parameter names
to the profile's `header_fields` names when calling `super().__init__()`. The profile field
names are the canonical internal names. Public APIs keep their existing parameter names.

### CLI Changes

#### New `types` command

```
jira-tool types [PROJECT]
```

- PROJECT defaults to `JIRA_DEFAULT_PROJECT` env var / config
- Queries `client.get_issue_types(project)`
- Displays as a Rich table: Name, Subtask (yes/no), Has Custom Profile (yes/no)

**API migration note:** The existing `client.get_issue_types()` uses the deprecated
`/rest/api/3/issue/createmeta` endpoint. Atlassian replaced this with
`/rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes` (paginated).
As part of this work, update `get_issue_types()` to use the new endpoint.
If the new endpoint is not available (older Jira instances), fall back to the old one.

#### Updated `create` command

```
jira-tool create --type Risk --summary "..." --project WPCW
```

Changes:
- Help text: `"Issue type — run 'jira-tool types' to see available types"`
- Validates type against Jira API before building (clear error for invalid types)
- Uses `get_profile(issue_type)` + `TypedBuilder` instead of if/else
- Default remains `Task`

#### No changes to `get`, `search`, `export`, `update`

These already handle any issue type — they read from the API and display whatever fields are present.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `builders/sections.py` | **Create** | Reusable section functions |
| `builders/profiles.py` | **Create** | `TYPE_PROFILES` dict + `get_profile()` |
| `builders/typed.py` | **Create** | `TypedBuilder` class |
| `builders/base.py` | **Modify** | Add `add_titled_section`, `add_header_info_panel` |
| `builders/epic.py` | **Modify** | Thin down to use sections, extend `TypedBuilder` |
| `builders/issue.py` | **Modify** | Thin down to use sections, extend `TypedBuilder` |
| `builders/subtask.py` | **Modify** | Thin down to use sections, extend `TypedBuilder` |
| `builders/__init__.py` | **Modify** | Export `TypedBuilder`, `get_profile` |
| `client.py` | **Modify** | Update `get_issue_types()` to new Jira API endpoint with fallback |
| `cli.py` | **Modify** | Add `types` command, update `create` routing + help text + type validation |
| `document/__init__.py` | **Modify** | Re-export new builders |
| `formatter.py` | **No change** | Already re-exports from document module |
| `tests/test_sections.py` | **Create** | Unit tests for all section functions |
| `tests/test_typed_builder.py` | **Create** | Tests for TypedBuilder + profiles |
| `tests/test_types_command.py` | **Create** | CLI test for `types` command |
| `tests/test_create_refactor.py` | **Create** | Tests for updated create routing |

## Testing Strategy

1. **Section functions** — Each section tested in isolation: call it on a `DocumentBuilder`, verify ADF output contains expected nodes
2. **Profiles** — `get_profile("risk")` returns risk profile, unknown type returns `_default`
3. **TypedBuilder** — Build a risk document, verify it contains header + all risk sections in order
4. **Backward compatibility** — Structural equivalence tests for all three wrappers:
   - `EpicBuilder(title, priority).add_description("x").build()` — same ADF structure
   - `IssueBuilder(title, component, story_points=3, epic_key="X-1").build()` — same ADF structure
   - `IssueBuilder(title, component).build()` — header omits story_points/epic (NEW behavior, intentional)
   - `SubtaskBuilder(title, parent_key="X-1").build()` — estimated_hours omitted (same as before)
   - `SubtaskBuilder(title, parent_key="X-1", estimated_hours=4.0).build()` — same ADF structure
5. **CLI types** — Mock `get_issue_types`, verify table output
6. **CLI create** — Mock API, test `--type Risk` uses correct profile, invalid type gives clear error

## Build Sequence

Ordered by actual dependency chain:

1. `builders/base.py` — add `add_titled_section`, `add_header_info_panel` helpers (no new deps)
2. `builders/profiles.py` — profiles dict + `get_profile()` + `FIELD_LABELS` (no deps on other new code)
3. `builders/sections.py` — section functions (depends on base helpers from step 1)
4. `builders/typed.py` — TypedBuilder (depends on sections, profiles, base)
5. Tests for 1-4
6. Refactor `epic.py`, `issue.py`, `subtask.py` to extend TypedBuilder
7. Backward compatibility tests (structural equivalence, not byte-for-byte)
8. `client.py` — update `get_issue_types()` to use new Jira API endpoint
9. `cli.py` — add `types` command, update `create` routing + help text + type validation
10. CLI tests
11. Rebuild + manual test with real Jira (`jira-tool types WPCW`, `jira-tool get WPCW-629`)
