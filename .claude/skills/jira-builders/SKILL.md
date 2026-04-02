---
name: jira-builders
description: |
  Guide for using jira-tool CLI correctly to create and manage Jira tickets with rich formatting.
  Use when working with Jira tickets, epics, risks, or exports. Triggers on "create Jira ticket",
  "create risk issue", "search Jira", "get Jira ticket", "export Jira data", "list epics",
  "risk assessment", or any Jira API operations. Supports typed issue creation via TypedBuilder
  with 4 profiles: epic, risk, sub-task, and default (Task/Story/Bug). Prevents common mistakes
  like trying to import jira_tool Python module or using curl unnecessarily.
  Works with jira-tool CLI command and environment variables (JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN).
category: jira-atlassian
difficulty: beginner
tags: [jira, cli, tickets, epics, risks, formatting, typed-builder]
version: 1.1.0
---

# Jira Ticket Management

Use `jira-tool` CLI for all Jira operations.

## Core Commands

```bash
# Get ticket
jira-tool get PROJ-370

# Search
jira-tool search 'project=PROJ AND status="To Do"'

# List epics
jira-tool epics --project PROJ

# Create epic
jira-tool create --project PROJ --type Epic --summary "Title"

# Create story under epic
jira-tool create --project PROJ --type Story --summary "Title" --parent PROJ-370

# Create subtask
jira-tool create --project PROJ --type Sub-task --summary "Title" --parent PROJ-371

# Export for analysis
jira-tool export --project PROJ --all --format jsonl -o data.jsonl
```

## Typed Issue Creation (TypedBuilder Profiles)

The CLI uses `TypedBuilder` internally to format descriptions based on issue type.
Four type profiles are available, each with distinct header fields and sections:

| Profile | Issue Types | Header Fields | Panel Style |
|---------|-----------|---------------|-------------|
| **epic** | Epic | priority, dependencies, services | warning |
| **risk** | Risk | likelihood, impact, overall_risk | warning |
| **sub-task** | Sub-task | parent, estimated_hours | info |
| **_default** | Task, Story, Bug, etc. | component, story_points, epic | info |

### Creating Risk Issues (CLI)

```bash
# Basic risk issue
jira-tool create --project PROJ --type Risk \
  --summary "CVE-2024-1234 in base image" \
  --description "Critical vulnerability found in production container base image"

# Risk issue with heredoc for detailed description
jira-tool create --project PROJ --type Risk \
  --summary "Third-party API rate limit exposure" \
  --description "$(cat <<'EOF'
Payment gateway API has undocumented rate limits that could cause
transaction failures during peak traffic periods.
EOF
)"
```

### Creating Risk Issues (Programmatic — TypedBuilder)

For richer risk documents with all risk-specific sections, use the Python API:

```python
from jira_tool.document import TypedBuilder

builder = TypedBuilder("risk", "CVE-2024-1234 in base image",
                       likelihood="Medium", impact="High", overall_risk="High")
builder.add_section("description", text="Critical CVE in production container base image")
builder.add_section("risk_assessment", likelihood="Medium", impact="High", overall="High")
builder.add_section("mitigation", strategies=[
    "Upgrade base image to patched version",
    "Enable runtime vulnerability scanning",
    "Add image signing to CI pipeline",
])
builder.add_section("acceptance_rationale",
    rationale="Risk accepted for 48h while patch is validated in staging")
builder.add_section("acceptance_criteria", criteria=[
    "Patched image deployed to all environments",
    "No new CVEs above MEDIUM severity",
    "Vulnerability scan passes in CI",
])
builder.add_section("monitoring_plan", steps=[
    "Daily vulnerability scan of running containers",
    "Alert on any new HIGH/CRITICAL CVEs",
    "Weekly review of patch status",
])
adf = builder.build()
```

**Risk profile sections:** `description`, `risk_assessment`, `mitigation`,
`acceptance_rationale`, `acceptance_criteria`, `monitoring_plan`

**MCP gap:** The MCP server (`create_issue` tool) only builds plain-text ADF.
For rich typed documents, use the CLI or programmatic `TypedBuilder` API.

## Rich Descriptions

Use heredoc for multi-line descriptions:

```bash
jira-tool create --project PROJ --type Epic \
  --summary "User Authentication" \
  --description "$(cat <<'EOF'
Implement OAuth2 authentication with session management.

**Problem Statement:**
Users cannot securely log in.

**Acceptance Criteria:**
- User can log in with email/password
- Session persists across refresh
- Logout invalidates sessions
EOF
)"
```

## Batch Operations

Shell scripts with jira-tool:

```bash
#!/bin/bash
EPIC=$(jira-tool create --project PROJ --type Epic \
  --summary "Parent Epic" --format json | jq -r '.key')

for task in "Task 1" "Task 2" "Task 3"; do
  jira-tool create --project PROJ --type Story \
    --summary "$task" --parent "$EPIC"
done
```

## Data Processing

Export and process with shell tools:

```bash
# Export tickets
jira-tool export --project PROJ --all --format jsonl -o tickets.jsonl

# Process with jq
jq -r 'select(.fields.status.name == "To Do") | .key' tickets.jsonl
```

## When to Use What

- **Single operation:** `jira-tool` directly
- **Batch operations:** Shell scripts with `jira-tool` in loops
- **Complex workflows:** Invoke `jira-ticket-manager` agent
- **Data analysis:** Export + process with jq/awk

## Requirements

- `jira-tool` CLI installed (check with `jira-tool --version`)
- Environment: `JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`

## Critical Anti-Patterns to Avoid

**DO NOT:**
1. Import jira_tool Python module - it's internal/private
   ```python
   # WRONG - This will fail
   from jira_tool import JiraClient
   ```

2. Use curl for Jira API unless jira-tool doesn't support the operation
   ```bash
   # WRONG - Fragile, error-prone
   curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" "$JIRA_BASE_URL/rest/api/3/search"
   ```

3. Create multiple scripts for same purpose (violates DRY principle)
   ```bash
   # WRONG - Multiple scripts for slight variations
   pull_tickets_basic.py, pull_tickets_filtered.py, pull_tickets_csv.py
   ```

**DO:**
1. Use jira-tool CLI for all operations
   ```bash
   # RIGHT - Use the CLI
   jira-tool search 'project=PROJ'
   ```

2. Use subprocess if you need programmatic access
   ```python
   # RIGHT - Call CLI from Python
   import subprocess
   result = subprocess.run(['jira-tool', 'get', 'PROJ-123'],
                          capture_output=True, text=True)
   ```

3. Use command-line flags for variations
   ```bash
   # RIGHT - One script with options
   jira-tool export --format csv --filter status=Open -o file.csv
   ```

## Supporting References

- **Quick Reference:** `~/.claude/skills/jira-builders/references/QUICK_REFERENCE.md` - Common CLI patterns and examples
- **Tool Selection:** `~/.claude/skills/jira-builders/references/TOOL_SELECTION.md` - When to use CLI vs agent vs curl
