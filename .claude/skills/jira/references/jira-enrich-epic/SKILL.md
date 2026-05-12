---
name: jira-enrich-epic
description: |
  Enriches Jira epics with comprehensive structure, ADF-formatted content, and child ticket
  analysis. Use when enhancing epic quality, adding detailed descriptions, analyzing epic
  composition, or structuring epic workflows. Triggers on "enrich epic", "epic structure",
  "epic details", "epic breakdown", or "organize epic".
---

# Jira Epic Enrichment

Specialized skill within the `/jira` uber-skill for epic management and enhancement.

## Quick Start

Enrich an existing epic:
```
/jira:enrich-epic PROJ-100
```

## What This Skill Does

- Analyzes epic structure and child tickets
- Adds comprehensive descriptions
- Applies ADF formatting
- Organizes child tickets by status
- Generates summary statistics
- Creates breakdown views

## See Also

- Parent skill: `/jira` — All Jira operations
- Related: `references/jira-batch-create/SKILL.md` — Creating tickets
- Reference: `../jira-document-formatting.md` — ADF patterns
