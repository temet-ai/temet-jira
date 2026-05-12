---
name: build-jira-document-format
description: |
  Creates complex ADF (Atlassian Document Format) documents using builder patterns, fluent APIs,
  and specialized templates for epics, risks, bugs, and feature requests. Use when creating
  sophisticated Jira descriptions, risk assessments, epics with structure, or rich content
  documents. Provides TypedBuilder with 4 type profiles (epic, risk, sub-task, _default),
  plus EpicBuilder and IssueBuilder for method chaining and pre-built templates.

  Trigger keywords: "ADF template", "document builder", "complex description", "fluent API",
  "epic structure", "risk issue", "risk assessment", "formatted issue", "rich content",
  "builder pattern", "TypedBuilder", "EpicBuilder", "IssueBuilder", "document template",
  "nested content", "advanced formatting", "typed builder profiles".
Works with Python 3.10+, temet_jira.document module, and Jira REST API v3.
category: jira-atlassian
difficulty: intermediate
tags: [jira, adf, builder-pattern, documentation, typed-builder, risk]
version: 1.1.0
---

# Build Jira Document Format (Advanced)

## Purpose

Master advanced Atlassian Document Format patterns for creating sophisticated, reusable Jira documents. Learn the builder pattern for fluent APIs, use `TypedBuilder` with type profiles (epic, risk, sub-task, _default) for structured documents, create specialized templates (EpicBuilder, IssueBuilder), design complex nested structures, and build document templates that scale from individual issues to epic planning and risk assessments. Transform raw content into professionally formatted Jira documents.

## Quick Start

Create a formatted epic with problem statement, technical details, and acceptance criteria:

```python
from temet_jira.formatter import EpicBuilder

# Create epic with builder
epic = EpicBuilder("Authentication Overhaul", "P0")
epic.add_problem_statement("Current auth is vulnerable to timing attacks")
epic.add_description("Implement OAuth2 with PKCE and secure session management")
epic.add_technical_details(
    requirements=[
        "PKCE flow support",
        "Session token encryption",
        "Rate limiting"
    ],
    code_example="""
    # OAuth2 flow
    token = oauth_client.get_token(code, pkce_verifier)
    session.set_secure_cookie(token)
    """
)
epic.add_acceptance_criteria([
    "All authentication tests pass",
    "Security audit complete",
    "Rate limiting works per RFC 6749"
])

# Get ADF for Jira API
adf = epic.build()
```

Or build step-by-step with the general-purpose builder:

```python
from temet_jira.formatter import JiraDocumentBuilder

doc = JiraDocumentBuilder()
doc.add_heading("Epic: Authentication System", 1)
doc.add_heading("Problem", 2)
doc.add_panel("warning",
    {"type": "paragraph", "content": [
        doc.add_text("Current authentication has security vulnerabilities")
    ]}
)
doc.add_heading("Approach", 2)
doc.add_bullet_list([
    "Implement OAuth2 with PKCE",
    "Use session token encryption",
    "Add rate limiting"
])
doc.add_heading("Acceptance Criteria", 2)
doc.add_ordered_list([
    "All tests pass",
    "Security audit complete",
    "Rate limiting implemented"
])

adf = doc.build()
```

## Instructions

### Step 1: Understand the Builder Pattern

The builder pattern solves the problem of constructing complex objects through method chaining.

**Why Builders?**

Without builder (verbose):
```python
# Manual ADF construction is error-prone and hard to read
doc = {
    "version": 1,
    "type": "doc",
    "content": [
        {
            "type": "heading",
            "attrs": {"level": 1},
            "content": [{"type": "text", "text": "Title"}]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Start: "},
                {"type": "text", "text": "Bold", "marks": [{"type": "bold"}]}
            ]
        }
    ]
}
```

With builder (readable):
```python
doc = JiraDocumentBuilder()
doc.add_heading("Title", 1)
doc.add_paragraph(
    doc.add_text("Start: "),
    doc.bold("Bold")
)
adf = doc.build()
```

**Builder Benefits**:
1. **Fluent API**: Chain methods for readability
2. **Safety**: Builders handle nesting automatically
3. **Reusability**: Extend builders for custom layouts
4. **Validation**: Catch errors early

### Step 2: Master the JiraDocumentBuilder

The general-purpose builder is your foundation:

**Method Chaining** (call methods in sequence):
```python
doc = JiraDocumentBuilder()
doc.add_heading("Title", 1) \
    .add_paragraph(doc.add_text("Introduction")) \
    .add_rule() \
    .add_heading("Section", 2) \
    .add_bullet_list(["Point 1", "Point 2"])

adf = doc.build()
```

**Key Methods**:

1. **Structural Elements**:
   ```python
   doc.add_heading("Text", level=1)      # Level 1-6
   doc.add_paragraph(content_nodes)       # Mixed content
   doc.add_rule()                         # Horizontal line
   ```

2. **Lists**:
   ```python
   doc.add_bullet_list(["Item 1", "Item 2"])
   doc.add_ordered_list(["First", "Second"], start=1)
   ```

3. **Code Blocks**:
   ```python
   doc.add_code_block("def hello(): pass", language="python")
   ```

4. **Panels** (colored boxes):
   ```python
   doc.add_panel("info",
       {"type": "paragraph", "content": [doc.add_text("Info panel")]}
   )
   # Types: info, note, warning, success, error
   ```

5. **Visual Elements**:
   ```python
   doc.add_rule()                         # Separator
   emoji = doc.add_emoji(":rocket:", "🚀")  # Emoji
   ```

**Text Content Helpers**:

```python
# Create formatted text nodes
doc.bold("Bold text")              # Returns text node with bold mark
doc.italic("Italic text")           # Returns text node with italic mark
doc.code("inline_code")             # Returns text node with code mark
doc.strikethrough("Deleted")        # Returns text node with strikethrough
doc.link("Click here", "https://...") # Returns text node with link
doc.add_text("Plain text")          # Plain text node
```

**Combining Formatting**:
```python
doc.add_paragraph(
    doc.bold("Important: "),
    doc.add_text("This is a ")
    doc.italic("complex"),
    doc.add_text(" message")
)
```

### Step 3: Create Specialized Builders for Common Patterns

For repeated structures, build specialized builders using subclassing or composition. Common patterns include:

- **Titled Panels**: Headings followed by colored panels for risks/benefits
- **Key-Value Pairs**: Structured specifications with bullet lists
- **Feature Lists**: Requirements with checkbox formatting

For full implementations, see `references/advanced-patterns.md`.

### Step 4: Use TypedBuilder for Profile-Based Documents

`TypedBuilder` (in `src/jira_tool/document/builders/typed.py`) composes ADF documents from type profiles. Each profile defines allowed sections, header fields, and display settings.

**4 Type Profiles** (defined in `src/jira_tool/document/builders/profiles.py`):

| Profile | Emoji | Header Fields | Sections |
|---------|-------|---------------|----------|
| **epic** | rocket | priority, dependencies, services | description, problem_statement, acceptance_criteria, implementation_details, edge_cases, testing_considerations, out_of_scope, success_metrics |
| **risk** | warning | likelihood, impact, overall_risk | description, risk_assessment, mitigation, acceptance_rationale, acceptance_criteria, monitoring_plan |
| **sub-task** | pushpin | parent, estimated_hours | description, steps, done_criteria |
| **_default** | clipboard | component, story_points, epic | description, implementation_details, acceptance_criteria |

Any unrecognized issue_type falls back to `_default`. Lookup is case-insensitive.

**Example: Risk Issue with TypedBuilder**:
```python
from temet_jira.document import TypedBuilder

builder = TypedBuilder("risk", "CVE-2024-1234 in base image",
                       likelihood="Medium", impact="High", overall_risk="High")
builder.add_section("description", text="Critical CVE found in production container")
builder.add_section("risk_assessment", likelihood="Medium", impact="High", overall="High")
builder.add_section("mitigation", strategies=[
    "Upgrade base image to patched version",
    "Enable runtime vulnerability scanning",
])
builder.add_section("acceptance_rationale",
    rationale="Risk accepted for 48h while patch is validated in staging")
builder.add_section("acceptance_criteria", criteria=[
    "Patched image deployed to all environments",
    "Vulnerability scan passes in CI",
])
builder.add_section("monitoring_plan", steps=[
    "Daily vulnerability scan of running containers",
    "Alert on any new HIGH/CRITICAL CVEs",
])
adf = builder.build()
```

**Example: Epic with TypedBuilder**:
```python
builder = TypedBuilder("epic", "Payment System Redesign",
                       priority="P0", dependencies="Bank API", services="Payments")
builder.add_section("description", text="Redesign payment processing pipeline")
builder.add_section("problem_statement", problem="Current system handles only credit cards")
builder.add_section("acceptance_criteria", criteria=["ACH support live", "Tests pass"])
adf = builder.build()
```

**Example: Sub-task with TypedBuilder**:
```python
builder = TypedBuilder("sub-task", "Add retry logic",
                       parent="PROJ-100", estimated_hours="4h")
builder.add_section("description", text="Implement exponential backoff for API calls")
builder.add_section("steps", steps=["Add retry decorator", "Configure backoff params", "Add tests"])
builder.add_section("done_criteria", criteria=["All API calls use retry", "Tests cover failure cases"])
adf = builder.build()
```

**Key methods:**
- `add_section(name, **kwargs)` - Add a section (raises `ValueError` if not in profile)
- `add_section_optional(name, **kwargs)` - Add section only if in profile (no error)

**MCP gap:** The MCP `create_issue` tool only builds plain-text ADF descriptions. For rich typed documents with sections and panels, use the CLI (`temet-jira create`) or programmatic `TypedBuilder` API.

### Step 5: Extend with Specialized Builders

Create purpose-built builders for complex documents:

**Example: EpicBuilder** (from codebase)
```python
from temet_jira.formatter import EpicBuilder

class EpicBuilder:
    """Pre-formatted epic template."""

    def __init__(self, title: str, priority: str = "P1"):
        self.title = title
        self.priority = priority
        self.builder = JiraDocumentBuilder()
        self._add_header()

    def _add_header(self):
        """Add standardized header."""
        self.builder.add_heading(f"🎯 {self.title}", 1)
        self.builder.add_paragraph(
            self.builder.bold("Priority: "),
            self.builder.add_text(self.priority)
        )

    def add_problem_statement(self, statement: str):
        """Add problem section."""
        self.builder.add_heading("Problem Statement", 2)
        self.builder.add_panel("warning", {
            "type": "paragraph",
            "content": [self.builder.add_text(statement)]
        })
        return self

    def add_acceptance_criteria(self, criteria: list[str]):
        """Add acceptance criteria."""
        self.builder.add_heading("Acceptance Criteria", 2)
        self.builder.add_ordered_list(criteria)
        return self

    def build(self):
        """Return ADF."""
        return self.builder.build()
```

**Usage**:
```python
epic = EpicBuilder("New Auth System", "P0")
epic.add_problem_statement("Current auth is insecure")
epic.add_acceptance_criteria([
    "OAuth2 implemented",
    "Tests pass",
    "Security audit complete"
])

adf = epic.build()
```

**Template Benefits**:
- Consistent structure across epics
- Enforces best practices
- Reduces boilerplate
- Easy to extend with custom methods

### Step 5: Design Complex Nested Structures

ADF supports hierarchical nesting for sophisticated layouts. For complex examples with risk assessment, multi-level headings, and combined formatting, see `references/advanced-patterns.md`.

### Step 6: Implement Builder Best Practices

For best practices including method chaining, lazy content, validation, and structure documentation, see `references/advanced-patterns.md`.

### Step 7: Reuse and Extend Builders

For builder inheritance patterns and specialized builders, see `references/advanced-patterns.md`.

## Examples

For comprehensive examples including:
- Creating structured epics with problem statements and acceptance criteria
- Complex feature requests with technical design and risk assessment
- Custom builders for bug reports with environment and reproduction steps

See `examples/examples.md` for full working code.

## Requirements

### Core Requirements
- **Python 3.10+** (for type hints and dataclass improvements)
- **temet_jira.formatter module** from this project containing:
  - `JiraDocumentBuilder` - General-purpose builder
  - `EpicBuilder` - Epic-specific template
  - `IssueBuilder` - Issue-specific template

### For Testing Builders
- **Jira REST API v3 access** (to submit built documents)
- **Environment variables**: `JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`
- **Test project** where you can create issues

### Recommended Tools
- **jira_adf_validator** (https://github.com/atlassian-community/jira-adf-validator):
  ```bash
  npm install -g jira-adf-validator
  echo '{"version":1,"type":"doc","content":[]}' | jira-adf-validator
  ```
- **Python json**: Built-in (for validating ADF structure)
- **curl**: For testing API submissions

## Supporting Files

- `examples/examples.md` - Complete working examples for epics, feature requests, and bug reports
- `references/advanced-patterns.md` - Complex nested structures, best practices, and builder inheritance

## See Also

- CLAUDE.md - Project configuration and patterns
- src/jira_tool/formatter.py - Full builder implementation reference
