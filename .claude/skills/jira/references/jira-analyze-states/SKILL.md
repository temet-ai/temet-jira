---
name: jira-analyze-states
description: |
  Analyzes Jira ticket state durations and workflow bottlenecks by calculating business hours
  spent in each workflow state (9 AM–5 PM weekdays). Use when identifying slow workflow states,
  measuring cycle time, analyzing state transitions, or optimizing delivery metrics.
  Triggers on "analyze state durations", "workflow analysis", "bottleneck detection",
  "cycle time analysis", "state transition history", or "workflow optimization".
---

# Jira State Duration Analysis

Specialized skill within the `/jira` uber-skill for analyzing workflow performance and identifying bottlenecks.

## Quick Start

Analyze a single ticket's workflow:
```
/jira-analyze-states PROJ-123
```

Analyze all tickets in a project:
```
/jira-analyze-states "project = PROJ AND created >= 2024-01-01"
```

## What This Skill Does

- Extracts state transition history from Jira changelog
- Calculates time spent in each workflow state
- Computes business hours (9 AM–5 PM, weekdays only)
- Identifies bottleneck states (longest durations)
- Generates cycle time metrics
- Exports results to CSV for analysis

## See Also

- Parent skill: `/jira` — All Jira operations
- Related: `references/jira-export-and-analyze-data/SKILL.md` — Data export patterns
- Reference: `../jira-state-analysis.md` — Detailed state analysis patterns
