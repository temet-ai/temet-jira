---
name: jira-batch-create
description: |
  Creates multiple Jira tickets from requirements lists with automatic parsing, ADF formatting,
  and epic linking. Use when bulk-creating tickets from specifications, converting requirements
  into tickets, planning sprints, or decomposing epics. Triggers on "batch create", "create multiple",
  "bulk create", "requirements list", "epic breakdown", or "sprint planning".
---

# Jira Batch Create

Specialized skill within the `/jira` uber-skill for creating multiple tickets efficiently.

## Quick Start

Create tickets from requirements file:
```
/jira:batch-create --requirements features.md --epic PROJ-100
```

## What This Skill Does

- Parses requirements (markdown, text, or CSV)
- Extracts ticket summaries and descriptions
- Applies automatic formatting (ADF)
- Links tickets to epics
- Assigns labels and components
- Validates before creation
- Handles errors and retries

## See Also

- Parent skill: `/jira` — All Jira operations
- Related: `references/jira-api/SKILL.md` — API patterns
- Reference: `../jira-batch-operations.md` — Detailed batch patterns
