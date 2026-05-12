---
name: jira-export-and-analyze-data
description: |
  Exports Jira issues with flexible filtering and analyzes data using CSV, JSON, or JSONL formats.
  Use when extracting bulk data, performing analysis, generating reports, or importing into
  external tools. Triggers on "export", "extract data", "bulk export", "data analysis",
  or "generate report".
---

# Jira Export and Analysis

Specialized skill within the `/jira` uber-skill for data extraction and reporting.

## Quick Start

Export tickets to CSV:
```
/jira:export "project = PROJ" --format csv
```

## What This Skill Does

- Exports with flexible filtering (JQL)
- Supports CSV, JSON, and JSONL formats
- Selects specific fields
- Handles pagination for large datasets
- Prepares data for external analysis
- Generates summaries and statistics

## See Also

- Parent skill: `/jira` — All Jira operations
- Related: `references/jira-analyze-states/SKILL.md` — State analysis
- Reference: `../jira-api-patterns.md` — API patterns
