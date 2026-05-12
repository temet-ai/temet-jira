# Jira API Patterns & Advanced Queries

## Overview

This reference covers advanced JQL queries, API field selection, pagination, and bulk operations for extracting and manipulating Jira data programmatically.

## Table of Contents

- JQL Query Language
- Field Selection & Expansion
- Pagination & Performance
- Bulk Operations
- Common Query Patterns
- Error Handling

---

## JQL Query Language

### Basic Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `status = "To Do"` |
| `!=` | Not equals | `status != Done` |
| `>` | Greater than | `priority > 3` |
| `<` | Less than | `created < 2024-01-01` |
| `>=` | Greater or equal | `updated >= 2024-01-01` |
| `<=` | Less or equal | `priority <= 2` |
| `~` | Contains | `summary ~ "bug"` |
| `!~` | Does not contain | `summary !~ "deprecated"` |
| `IN` | In list | `status IN ('To Do', 'In Progress')` |
| `NOT IN` | Not in list | `priority NOT IN (1, 2)` |

### Logical Operators

```
AND     - Both conditions must be true
OR      - Either condition can be true
NOT     - Negate condition
()      - Group conditions
```

### Field References

**Standard Fields:**
- `project` — Project key (e.g., `PROJ`, `PROJ`)
- `status` — Workflow status (To Do, In Progress, Done, etc.)
- `assignee` — Person assigned to ticket
- `reporter` — Person who created ticket
- `priority` — Priority level (Highest, High, Medium, Low, Lowest)
- `type` — Issue type (Story, Task, Bug, Epic)
- `created` — Creation date
- `updated` — Last update date
- `summary` — Ticket title (searchable)
- `description` — Ticket body (searchable)
- `labels` — Tags/categories
- `sprint` — Current sprint
- `parent` — Epic or parent ticket
- `component` — Project component

**Date Format:**
All dates use ISO 8601: `YYYY-MM-DD` or Unix timestamps

### Advanced Query Patterns

**Current User:**
```
assignee = currentUser()           # Assigned to me
reporter = currentUser()           # Created by me
assignee in (currentUser(), "bob") # Me or Bob
```

**Date Ranges:**
```
created >= 2024-01-01 AND created <= 2024-12-31  # Full year 2024
updated >= -7d                                    # Updated in last 7 days
created >= -30d AND status = "In Progress"       # Recent + active
```

**Text Search:**
```
summary ~ "authentication"                    # Title contains word
description ~ "OAuth"                        # Description contains
summary ~ "login" OR summary ~ "auth"        # Multiple keywords
summary !~ "deprecated"                      # Exclude pattern
```

**Nested Conditions:**
```
(project = PROJ AND status = Open) OR (project = OTHER AND priority = High)
NOT (status = Done OR status = "Won't Do")
assignee = currentUser() AND (priority = High OR parent = PROJ-100)
```

**Sprint Queries:**
```
sprint in openSprints()           # Current/open sprints
sprint in futureSprints()         # Upcoming sprints
sprint = SPRINT-123               # Specific sprint
```

**Epic Queries:**
```
parent = PROJ-100                 # All tickets in epic
type = Epic AND assignee = bob    # Epics assigned to Bob
parent is EMPTY                   # Orphaned tickets (no epic)
```

---

## Field Selection & Expansion

### Basic Field Selection

Minimize payload by selecting only needed fields:

```bash
# Get all fields (default, slower)
temet-jira search "project = PROJ" --format json

# Select specific fields (faster, smaller)
temet-jira search "project = PROJ" \
  --fields key,summary,status,assignee,priority \
  --format json
```

### Common Field Combinations

**Quick Overview:**
```
key, summary, status, assignee, priority, created
```

**Detailed View:**
```
key, summary, description, status, assignee, reporter, priority,
labels, components, created, updated, parent, epic
```

**State Analysis:**
```
key, summary, status, created, updated, changelog
(Use --expand changelog for state transition history)
```

### Field Expansion

Expand related data without additional API calls:

```bash
# Include changelog for state analysis
--expand changelog

# Include full object details (slower)
--expand changelog,history,worklog

# Include custom fields
--fields key,summary,customfield_10000,customfield_10001
```

---

## Pagination & Performance

### Pagination Basics

Jira API default: 50 results per page, max 50

```bash
# Get first 50
temet-jira search "project = PROJ"

# Get specific page (requires offset math)
# Page 2: startAt=50, maxResults=50
# Page 3: startAt=100, maxResults=50
```

### Large Result Sets

For queries returning >1000 results:

```bash
# Strategy 1: Time-window pagination
# Divide by date ranges
temet-jira search "project = PROJ AND created >= 2024-01-01 AND created < 2024-04-01"
temet-jira search "project = PROJ AND created >= 2024-04-01 AND created < 2024-07-01"

# Strategy 2: Export with streaming
temet-jira export "project = PROJ" --format jsonl --output results.jsonl
# (Each line is one ticket - no memory overhead)

# Strategy 3: Status-based filtering
temet-jira search "project = PROJ AND status = Done AND updated >= 2024-01-01"
temet-jira search "project = PROJ AND status IN ('To Do', 'In Progress')"
```

### Performance Tips

- **Select fields strategically** — Only fetch what you need
- **Use time ranges** — Divide large queries by date
- **Filter early** — Let Jira API do filtering, not post-processing
- **Export to files** — For analysis, use CSV/JSON export then process locally
- **Avoid full-text search at scale** — `summary ~` and `description ~` are slower
- **Cache results** — Store API responses locally if querying same data repeatedly

---

## Bulk Operations

### Batch Create Tickets

```bash
# Create multiple tickets from requirements
temet-jira create-batch \
  --project PROJ \
  --requirements requirements.md \
  --epic PROJ-100 \
  --format json \
  --output created-tickets.json
```

**Input Format (requirements.md):**
```
# Q1 Authentication System

## OAuth2 Implementation
- Implement OAuth2 token endpoint
- Add refresh token mechanism
- Validate token signatures

## API Security
- Add rate limiting to endpoints
- Implement request signing
- Add audit logging
```

### Batch Update Tickets

```bash
# Update multiple tickets (status, labels, priority)
temet-jira update-batch \
  --query "project = PROJ AND status = 'To Do' AND priority = High" \
  --status "In Progress" \
  --labels "urgent" \
  --output updated-tickets.json
```

### Batch Export

```bash
# Export to multiple formats
temet-jira export "project = PROJ AND created >= 2024-01-01" \
  --format csv \
  --output export.csv

# Export with custom fields
temet-jira export "project = PROJ" \
  --fields key,summary,status,assignee,parent,labels \
  --format json \
  --output export.json
```

---

## Common Query Patterns

### By Project & Status

```
# All open work in project
project = PROJ AND status IN ('To Do', 'In Progress')

# Done this quarter
project = PROJ AND status = Done AND updated >= -90d

# All issues by type
project = PROJ AND type = Task
project = PROJ AND type = Bug
```

### By Assignee

```
# My tickets
assignee = currentUser()

# Unassigned high-priority
assignee is EMPTY AND priority = High

# Assigned to team members
assignee in (alice, bob, charlie)

# Not assigned to me
assignee != currentUser()
```

### By Epic/Component

```
# All features in epic
parent = PROJ-100

# Authentication component
component = "Authentication"

# Cross-epic overview
type = Epic AND project = PROJ
```

### By Time

```
# Created this week
created >= -7d

# Updated this month
updated >= -30d

# Due date approaching
duedate <= +7d AND duedate >= -0d

# Created between dates
created >= 2024-01-01 AND created <= 2024-03-31
```

### Complex Workflows

```
# High-priority bugs not started
type = Bug AND priority = High AND status = "To Do"

# Long-running tickets (potential blockers)
status = "In Progress" AND updated <= -14d

# Completed this sprint by component
sprint in openSprints() AND status = Done AND component = Auth

# Epics with incomplete children
type = Epic AND parent is EMPTY AND
  (status != Done OR (parent = KEY AND parent.status != Done))
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid JQL syntax | Check operator spelling, quote strings |
| 401 Unauthorized | Invalid credentials | Verify API token/auth |
| 403 Forbidden | Insufficient permissions | Request access to project |
| 404 Not Found | Project/field doesn't exist | Check project key, custom field ID |
| 429 Too Many Requests | Rate limited | Reduce request frequency, add delays |

### Retry Strategy

```bash
# Exponential backoff for transient errors
Attempt 1: Immediate
Attempt 2: Wait 1 second
Attempt 3: Wait 2 seconds
Attempt 4: Wait 4 seconds
Max attempts: 5
```

### Validation

Always validate:
- Project key exists
- Custom field IDs are correct (format: `customfield_XXXXX`)
- Date formats are ISO 8601
- String values are quoted
- JQL syntax is correct (test in Jira UI first)
