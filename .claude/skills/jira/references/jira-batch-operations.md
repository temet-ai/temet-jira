# Jira Batch Operations & Requirements Conversion

## Overview

Batch operations enable creating, updating, or managing multiple Jira tickets efficiently. This guide covers converting requirements into tickets, handling bulk creation, and managing batch workflows.

## Table of Contents

- Batch Create from Requirements
- Input Formats
- Field Mapping
- Epic Linking
- Label Assignment
- Validation & Error Handling
- Workflow Examples

---

## Batch Create from Requirements

### When to Use Batch Create

Use batch create when you have:
- Requirements breakdown (feature spec)
- Epic structure to implement
- Sprint planning list
- Issue decomposition
- Backlog refinement

**Benefits:**
- Single command creates 10-100 tickets
- Automatic ADF formatting
- Consistent field values
- Epic linking
- Label assignment
- Parallel creation (faster)

### Basic Workflow

```bash
# 1. Prepare requirements in markdown
cat > q1-features.md << 'EOF'
# Q1 Authentication System

## OAuth2 Implementation
- Implement OAuth2 token endpoint
- Add refresh token mechanism
- Validate token signatures

## API Security
- Add rate limiting to endpoints
- Implement request signing
- Add audit logging
EOF

# 2. Create tickets from requirements
temet-jira batch-create \
  --project PROJ \
  --requirements q1-features.md \
  --epic PROJ-100 \
  --labels "authentication" "security" \
  --format json \
  --output created-tickets.json

# 3. Review output
cat created-tickets.json | jq '.[] | {key, summary, epic}'
```

**Output:**
```json
[
  {"key": "PROJ-456", "summary": "Implement OAuth2 token endpoint", "epic": "PROJ-100"},
  {"key": "PROJ-457", "summary": "Add refresh token mechanism", "epic": "PROJ-100"},
  {"key": "PROJ-458", "summary": "Validate token signatures", "epic": "PROJ-100"},
  {"key": "PROJ-459", "summary": "Add rate limiting to endpoints", "epic": "PROJ-100"},
  {"key": "PROJ-460", "summary": "Implement request signing", "epic": "PROJ-100"},
  {"key": "PROJ-461", "summary": "Add audit logging", "epic": "PROJ-100"}
]
```

---

## Input Formats

### Markdown Format (Recommended)

Hierarchical structure with sections and bullet points:

```markdown
# Epic Name
Epic-level description

## Feature/Component Name
Optional description

### Optional Subsection
- Ticket summary 1
- Ticket summary 2

## Another Feature
- Related ticket
  - Sub-ticket (creates parent-child)
```

**Parser Rules:**
- `# Title` → Epic name (if no epic specified)
- `## Heading` → Feature group (optional)
- `- Item` → Create ticket with summary
- `  - Nested` → Create as subtask

**Example:**
```markdown
# User Management System

## Authentication
- Implement login endpoint
- Add password reset flow
- Enable multi-factor authentication
  - TOTP implementation
  - SMS verification

## User Profile
- Create profile management page
- Add avatar upload
- Enable profile editing
```

### Text List Format

Simple line-by-line, one ticket per line:

```
Implement OAuth2 token endpoint
Add refresh token mechanism
Validate token signatures
Add rate limiting to endpoints
Implement request signing
Add audit logging
```

### CSV Format

For complex requirements with metadata:

```csv
summary,description,issue_type,priority
Implement OAuth2 token endpoint,Support OAuth2 client credentials flow,Task,High
Add refresh token mechanism,Implement refresh token rotation,Task,High
Validate token signatures,Verify JWT signatures using public keys,Task,Medium
```

---

## Field Mapping

### Auto-Detected Fields

| Input | Maps To | Logic |
|-------|---------|-------|
| `# Title` | Epic name | Top-level heading |
| `## Section` | Component/Label | Mid-level grouping |
| `- Summary` | Ticket summary | Bullet point |
| `[description]` | Description | Indented paragraph below summary |

### Overrideable Fields

```bash
temet-jira batch-create \
  --requirements input.md \
  --project PROJ \
  --issue-type "Story" \        # Default: Task
  --priority "High" \            # Default: Medium
  --assignee "alice" \           # Optional
  --sprint "SPRINT-45" \         # Optional
  --component "Auth" \           # Optional
  --labels "feature" "ui" \      # Optional
  --epic "PROJ-100"              # Optional
```

### Custom Field Mapping

For non-standard fields, include in input:

```markdown
# Feature
Custom field: Value
- Ticket 1
- Ticket 2
```

Parser extracts custom fields and applies to all tickets in section.

---

## Epic Linking

### Link to Existing Epic

```bash
temet-jira batch-create \
  --requirements features.md \
  --epic PROJ-100 \
  --output created.json
```

All created tickets link to epic `PROJ-100`.

### Create Epic First, Then Tickets

```bash
# 1. Create epic
EPIC=$(temet-jira create-epic \
  --project PROJ \
  --name "Q1 Features" \
  --output json | jq -r '.key')

# 2. Create tickets linked to epic
temet-jira batch-create \
  --requirements features.md \
  --epic $EPIC \
  --output created.json
```

### Hierarchical Structure

Create parent-child relationships:

```markdown
# Parent Task
- Child task 1
  - Subtask 1a
  - Subtask 1b
- Child task 2
```

Creates:
- Parent ticket (PROJ-100)
  - Child 1 (PROJ-101) — parent: PROJ-100
    - Sub 1a (PROJ-103) — parent: PROJ-101
    - Sub 1b (PROJ-104) — parent: PROJ-101
  - Child 2 (PROJ-102) — parent: PROJ-100

---

## Label Assignment

### Single Label Set

Apply same labels to all tickets:

```bash
temet-jira batch-create \
  --requirements input.md \
  --labels "feature" "backend" "p0"
```

Result: Each ticket gets all three labels.

### Section-Specific Labels

Define labels per section in markdown:

```markdown
# Feature Set

## Backend Tasks
[Labels: backend, optimization]
- Optimize database queries
- Add caching layer

## Frontend Tasks
[Labels: frontend, ui]
- Redesign dashboard
- Fix mobile layout
```

Parser recognizes `[Labels: ...]` and applies to section.

### Label from Hierarchy

Auto-assign labels based on structure:

```bash
temet-jira batch-create \
  --requirements input.md \
  --auto-labels \
  --labels-from-sections
```

Using:
```markdown
# Feature Set
## Authentication [auth]
- Implement OAuth2
- Add MFA
```

Result:
- OAuth2 ticket gets: `feature-set`, `authentication`, `auth`
- MFA ticket gets: `feature-set`, `authentication`, `auth`

---

## Validation & Error Handling

### Pre-flight Checks

Before creating, validate:

```bash
temet-jira batch-create \
  --requirements input.md \
  --dry-run \
  --output validation.json
```

Output shows what would be created without actually creating:

```json
{
  "total": 6,
  "valid": 6,
  "invalid": 0,
  "tickets": [
    {"summary": "Ticket 1", "valid": true},
    {"summary": "Ticket 2", "valid": true}
  ],
  "warnings": []
}
```

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Empty summary | Bullet point has no text | Add summary text |
| No project | --project not specified | Add `--project PROJ` |
| Invalid epic | Epic key doesn't exist | Check epic key spelling |
| Duplicate summary | Multiple identical summaries | Make summaries unique |
| Field too long | Summary exceeds limit | Shorten to <255 chars |

### Error Recovery

On partial failure:

```bash
# Retry failed tickets
temet-jira batch-create \
  --requirements input.md \
  --retry-failed \
  --output retry.json
```

Output separates succeeded from failed:

```json
{
  "succeeded": [{"key": "PROJ-100"}, ...],
  "failed": [{"summary": "...", "error": "..."}, ...],
  "total_succeeded": 5,
  "total_failed": 1
}
```

---

## Workflow Examples

### Example 1: Simple Feature Breakdown

**Input (features.md):**
```markdown
# Authentication System

## Core Implementation
- Set up authentication service
- Implement user database
- Add session management

## Security
- Add password hashing
- Implement CORS
- Add rate limiting

## Testing
- Write authentication tests
- Add integration tests
- Security audit
```

**Command:**
```bash
temet-jira batch-create \
  --requirements features.md \
  --project PROJ \
  --issue-type Story \
  --priority High \
  --labels "v1.0" "backend"
```

**Result:** 9 tickets created in PROJ project

---

### Example 2: Epic-Driven Planning

**Input (epic-breakdown.md):**
```markdown
# Payment Integration

## Provider: Stripe
- Research Stripe API
- Implement Stripe integration
- Add Stripe webhooks
- Test with production keys

## Provider: PayPal
- Research PayPal API
- Implement PayPal integration
- Test PayPal webhooks

## Testing & Security
- Add payment security tests
- Compliance review
- PCI-DSS verification
```

**Command:**
```bash
temet-jira create-epic \
  --name "Payment Integration" \
  --description "Q2 payment gateway work" \
  --project PROJ \
  --output epic.json

EPIC_KEY=$(cat epic.json | jq -r '.key')

temet-jira batch-create \
  --requirements epic-breakdown.md \
  --epic $EPIC_KEY \
  --project PROJ \
  --component "Payments"
```

**Result:** Epic created + 10 tickets linked to it

---

### Example 3: Sprint Planning

**Input (sprint.md):**
```markdown
# Sprint 45 Tasks

## High Priority
- Fix critical memory leak
- Add missing API endpoint
- Update documentation

## Medium Priority
- Refactor auth module
- Improve error handling
- Add unit tests

## Nice to Have
- Performance optimization
- Code cleanup
- Dependency update
```

**Command:**
```bash
temet-jira batch-create \
  --requirements sprint.md \
  --project PROJ \
  --sprint "SPRINT-45" \
  --labels "sprint-45"
```

**Result:** Tickets auto-assigned to sprint

---

## Best Practices

**Planning:**
- One requirement = one ticket (no compound statements)
- Clear, actionable summaries (not vague)
- Logical grouping by feature/component
- Realistic scope for completion

**Execution:**
- Always run `--dry-run` first for large batches
- Review output before confirming
- Link to epic early (simplifies tracking)
- Use consistent labels for reporting

**Follow-up:**
- Add acceptance criteria to each ticket
- Link related tickets (blocks, depends on)
- Assign to team members
- Plan sprint/milestone per epic
