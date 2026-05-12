---
description: Analyze ticket state durations for workflow insights
argument-hint: [jql-query or ticket-key] [optional: date-range]
---

# Analyze Ticket State Durations

@jira-ticket-manager

## Task
Analyze state durations for: $ARGUMENTS

## Requirements
1. Parse the query/ticket key and date range (if provided)
2. Fetch tickets with changelog data using `--expand changelog`
3. Use the StateDurationAnalyzer to calculate:
   - Time spent in each state (calendar days)
   - Business hours (9 AM - 5 PM, weekdays only)
   - State transition history
4. Export results to CSV format
5. Provide summary statistics:
   - Average time in each state
   - Bottleneck states (longest durations)
   - Total cycle time
6. Save output file and provide path

## Common Analysis Patterns
- **Single ticket**: "PROJ-123"
- **Project range**: "project = PROJ AND created >= 2024-01-01"
- **Sprint**: "sprint in openSprints()"
- **Epic**: "parent = PROJ-100"

## Workflow

1. Export issues: `temet-jira search "[JQL]" --expand changelog --format json --output issues.json`
2. Analyze: `temet-jira analyze state-durations issues.json --output analysis.csv --business-hours`
3. Provide insights from the analysis

## Output Format

After analysis, provide:

- Path to generated CSV file
- Summary statistics
- Key insights (bottlenecks, long-running tickets, etc.)
- Recommendations for workflow improvement
