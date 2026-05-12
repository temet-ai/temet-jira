# Jira Tool Usage Guide

Practical examples and common use cases for the `temet-jira` CLI.

## Table of Contents

- [Running Commands](#running-commands)
- [Common Workflows](#common-workflows)
- [Advanced Filtering](#advanced-filtering)
- [Working with Epics](#working-with-epics)
- [Data Export & Analysis](#data-export--analysis)
- [Workflow State Analysis](#workflow-state-analysis)
- [Team Collaboration](#team-collaboration)
- [Tips & Best Practices](#tips--best-practices)

## Running Commands

Examples use `temet-jira [command]`. Install with `uv tool install temet-jira` if you haven't yet.

## Common Workflows

### Daily Standup Prep

Get your active work and recently updated issues:

```bash
# Your issues in progress
temet-jira export --assignee "me" --status "In Progress"

# Issues you updated recently
temet-jira search "assignee = currentUser() AND updated >= -1d"

# Summary of all your active work
temet-jira export --assignee "me" --jql "status NOT IN (Done, Closed)"
```

### Sprint Planning

Review and organize sprint work:

```bash
# Backlog items for planning
temet-jira export --status "To Do" --priority High --format table

# Current sprint issues
temet-jira search "sprint in openSprints()" --format json -o sprint.json

# Completed work this sprint
temet-jira export --status Done --created "-14d" --format csv -o completed.csv

# Unassigned tasks
temet-jira search "project = PROJ AND assignee is EMPTY AND type = Task"
```

### Bug Triage

Manage and prioritize bugs:

```bash
# All open bugs
temet-jira export --type Bug --jql "resolution = Unresolved"

# High priority bugs
temet-jira export --type Bug --priority High --format csv -o critical_bugs.csv

# Recent bugs (last 7 days)
temet-jira export --type Bug --created "-7d" --format table

# Bugs by assignee
temet-jira export --type Bug --group-by assignee --stats
```

### Release Management

Track release progress:

```bash
# All issues in epic
temet-jira epic-details PROJ-100 --show-children --format json -o release.json

# Issues by status
temet-jira export --epic PROJ-100 --group-by status --stats

# Remaining work
temet-jira search "Epic Link = PROJ-100 AND status NOT IN (Done, Closed)"

# Export for release notes
temet-jira export --epic PROJ-100 --status Done --format csv -o release_notes.csv
```

### Quick Updates

Common update operations:

```bash
# Move to in progress and assign to yourself
temet-jira update PROJ-123 --status "In Progress" --assignee "me@example.com"

# Mark as high priority
temet-jira update PROJ-123 --priority High

# Add labels for tracking
temet-jira update PROJ-123 --labels "urgent,security,backend"

# Add comment with update
temet-jira comment PROJ-123 -m "Working on this now, ETA tomorrow"
```

## Advanced Filtering

### Date-Based Filtering

```bash
# Issues created today
temet-jira export --created "today"

# Issues created this week
temet-jira search "created >= startOfWeek()"

# Issues created in last 7 days
temet-jira export --created "-7d"

# Issues created in January 2024
temet-jira search "created >= 2024-01-01 AND created <= 2024-01-31"

# Recently updated (last hour)
temet-jira search "updated >= -1h"

# Stale issues (not updated in 30 days)
temet-jira search "updated <= -30d AND status NOT IN (Done, Closed)"
```

### Complex JQL Queries

```bash
# Multiple conditions with AND
temet-jira search "project = PROJ AND status = 'In Progress' AND assignee = currentUser()"

# Multiple conditions with OR
temet-jira search "priority = High OR priority = Highest"

# Combining AND/OR with parentheses
temet-jira search "project = PROJ AND (status = 'In Progress' OR status = Review) AND priority = High"

# NOT operator
temet-jira search "project = PROJ AND status NOT IN (Done, Closed, Cancelled)"

# IN operator for multiple values
temet-jira search "priority IN (High, Highest) AND type IN (Bug, 'Production Issue')"

# Text search
temet-jira search "project = PROJ AND summary ~ 'authentication'"
temet-jira search "description ~ 'database migration'"

# Custom field filtering
temet-jira search "project = PROJ AND 'Story Points' >= 5"

# Empty/null checks
temet-jira search "assignee is EMPTY AND priority = High"
temet-jira search "'Due Date' is not EMPTY"
```

### Component & Label Filtering

```bash
# Issues in specific component
temet-jira export --component "Backend Services"

# Multiple components (use JQL)
temet-jira search "component IN ('Backend Services', 'Frontend')"

# Issues with specific label
temet-jira search "labels = urgent"

# Issues with any of multiple labels
temet-jira search "labels IN (urgent, security, performance)"

# Issues without labels
temet-jira search "labels is EMPTY"
```

## Working with Epics

### Epic Discovery

```bash
# List all epics in project
temet-jira epics --project PROJ

# Export epic list as JSON
temet-jira epics --project PROJ --format json -o epics.json

# Find epics by name
temet-jira search "project = PROJ AND type = Epic AND summary ~ 'API'"
```

### Epic Analysis

```bash
# Get epic with all children
temet-jira epic-details PROJ-100 --show-children

# Export epic structure as JSON
temet-jira epic-details PROJ-100 --show-children --format json -o epic_structure.json

# Get issues in epic by status
temet-jira search "'Epic Link' = PROJ-100" --format table

# Count issues in epic
temet-jira search "'Epic Link' = PROJ-100" --jql "Epic Link = PROJ-100" --stats
```

### Epic Progress Tracking

```bash
# Epic completion status
temet-jira export --jql "'Epic Link' = PROJ-100" --group-by status --stats

# Remaining work in epic
temet-jira search "'Epic Link' = PROJ-100 AND status NOT IN (Done, Closed)"

# Completed items
temet-jira search "'Epic Link' = PROJ-100 AND status = Done" --format csv -o completed.csv

# Issues by assignee
temet-jira export --jql "'Epic Link' = PROJ-100" --group-by assignee --stats
```

## Data Export & Analysis

### Export Strategies

**Small Dataset (< 50 issues):**
```bash
# Use table for quick viewing
temet-jira export --project PROJ --format table

# Or JSON for further processing
temet-jira export --project PROJ --format json -o issues.json
```

**Medium Dataset (50-500 issues):**
```bash
# JSON for readability
temet-jira export --project PROJ --all --format json -o all_issues.json

# CSV for spreadsheet analysis
temet-jira export --project PROJ --all --format csv -o all_issues.csv
```

**Large Dataset (500+ issues):**
```bash
# JSONL for efficiency (recommended)
temet-jira export --project PROJ --all --format jsonl -o all_issues.jsonl

# Process line by line
cat all_issues.jsonl | jq -r '.key'
```

### Filtered Exports

```bash
# Active work across team
temet-jira export --status "In Progress" --all --format csv -o active_work.csv

# High priority backlog
temet-jira export --status "To Do" --priority High --format json -o backlog.json

# All bugs for analysis
temet-jira export --type Bug --all --format jsonl -o all_bugs.jsonl

# Issues by component
temet-jira export --component "Backend Services" --format csv -o backend.csv
```

### Grouping & Statistics

```bash
# Issues by assignee
temet-jira export --group-by assignee --stats

# Issues by status
temet-jira export --group-by status --stats

# Issues by priority
temet-jira export --group-by priority --stats

# Export grouped data as CSV
temet-jira export --group-by assignee --format csv -o by_assignee.csv
```

## Workflow State Analysis

### Analyzing State Durations

Understand how long issues spend in each workflow state:

**Step 1: Export with changelog**
```bash
# Export issues with full history
temet-jira export --project PROJ --expand changelog --format json -o issues_with_history.json

# Or for specific issues
temet-jira search "project = PROJ AND created >= -30d" --expand changelog --format json -o recent_issues.json
```

**Step 2: Analyze durations**
```bash
# Generate duration analysis
temet-jira analyze state-durations issues_with_history.json -o state_durations.csv
```

**Step 3: Review results**
```bash
# View in spreadsheet application
open state_durations.csv

# Or use command line tools
cat state_durations.csv | column -t -s,
```

### Interpreting Results

The analysis produces a CSV with:
- **issue_key** - The issue identifier
- **state** - Workflow state name
- **duration_calendar_days** - Total days (including weekends)
- **duration_business_hours** - Hours during business time (9 AM - 5 PM, weekdays)

**Example uses:**
- Identify bottlenecks (states with longest durations)
- Calculate cycle time (sum of all state durations)
- Compare business hours vs calendar days
- Track workflow efficiency over time

### Common Analysis Patterns

```bash
# Analyze recent sprint
temet-jira search "sprint = 'Sprint 10'" --expand changelog --format json -o sprint10.json
temet-jira analyze state-durations sprint10.json -o sprint10_durations.csv

# Analyze specific epic
temet-jira search "'Epic Link' = PROJ-100" --expand changelog --format json -o epic100.json
temet-jira analyze state-durations epic100.json -o epic100_durations.csv

# Analyze bugs for triage performance
temet-jira export --type Bug --created "-30d" --expand changelog --format json -o bugs.json
temet-jira analyze state-durations bugs.json -o bug_durations.csv
```

## Team Collaboration

### Reviewing Team Work

```bash
# Team capacity view
temet-jira export --jql "assignee is not EMPTY AND status NOT IN (Done, Closed)" --group-by assignee

# Unassigned issues
temet-jira search "project = PROJ AND assignee is EMPTY" --format table

# Overdue items (with due date)
temet-jira search "due < now() AND status NOT IN (Done, Closed)"

# Blocked items
temet-jira search "status = Blocked" --format csv -o blocked_items.csv
```

### Code Review Workflow

```bash
# Issues in review
temet-jira export --status Review --format table

# Your items needing review
temet-jira export --assignee "me" --status Review

# Add review comment
temet-jira comment PROJ-123 -m "LGTM, approved for merge"

# Move to done after merge
temet-jira update PROJ-123 --status Done
```

### Handoffs & Reassignment

```bash
# Check before handoff
temet-jira get PROJ-123

# Add handoff comment
temet-jira comment PROJ-123 -m "Handing off to @john - context: implemented auth, tests passing"

# Reassign
temet-jira update PROJ-123 --assignee "john@example.com"
```

## Tips & Best Practices

### Performance Optimization

**Use JSONL for large exports:**
```bash
# More efficient for 100+ issues
temet-jira export --project PROJ --all --format jsonl -o large_export.jsonl
```

**Limit results when exploring:**
```bash
# Use --max-results for quick checks
temet-jira search "project = PROJ" --max-results 10
```

**Use specific fields to reduce payload:**
```bash
# Only get what you need
temet-jira search "project = PROJ" --fields key,summary,status
```

### Automation & Scripting

**Batch processing:**
```bash
# Export, process, update
temet-jira export --status "To Do" --format json -o todo.json

# Parse and update each
cat todo.json | jq -r '.issues[].key' | while read key; do
  temet-jira update "$key" --priority High
done
```

**Daily reports:**
```bash
#!/bin/bash
# daily_report.sh
DATE=$(date +%Y-%m-%d)
temet-jira export --assignee "me" --format csv -o "report_${DATE}.csv"
echo "Report saved to report_${DATE}.csv"
```

**Integration with other tools:**
```bash
# Export to JSON for processing
temet-jira export --project PROJ --format json -o issues.json

# Process with jq
cat issues.json | jq '.issues[] | select(.fields.priority.name == "High")'

# Convert to another format
cat issues.json | jq -r '.issues[] | [.key, .fields.summary] | @csv'
```

### Error Handling

**Check for errors:**
```bash
# Save output and check exit code
temet-jira get PROJ-123 > output.txt
if [ $? -eq 0 ]; then
  echo "Success"
else
  echo "Failed" >&2
fi
```

**Validate before batch operations:**
```bash
# Check if issue exists first
temet-jira get PROJ-123 > /dev/null 2>&1
if [ $? -eq 0 ]; then
  temet-jira update PROJ-123 --status Done
fi
```

### Working with Different Environments

**Multiple Jira instances:**
```bash
# Use different env files
export $(grep -v '^#' .env.production | xargs)
temet-jira export --project PROJ --format csv -o prod_issues.csv

export $(grep -v '^#' .env.staging | xargs)
temet-jira export --project PROJ --format csv -o staging_issues.csv
```

**Project-specific defaults:**
```bash
# Set in .env file
JIRA_DEFAULT_PROJECT=MYTEAM
JIRA_DEFAULT_COMPONENT="Backend Services"

# Then use without specifying
temet-jira export --format table
```

### Output Formatting Tips

**Pretty print JSON:**
```bash
# Already pretty by default
temet-jira get PROJ-123 --format json

# Or pipe through jq for custom formatting
temet-jira search "project = PROJ" --format json | jq '.issues[] | {key, summary: .fields.summary}'
```

**CSV for Excel:**
```bash
# Export as CSV
temet-jira export --project PROJ --format csv -o issues.csv

# Open in Excel (macOS)
open -a "Microsoft Excel" issues.csv

# Or import into Google Sheets
```

**Table output for terminal:**
```bash
# Default table format is terminal-friendly
temet-jira export --status "In Progress"

# Combine with less for pagination
temet-jira export --all | less
```

### Keyboard Shortcuts & Aliases

Add to your `.zshrc` or `.bashrc`:

```bash
# Quick aliases
alias jt="temet-jira"
alias jtg="temet-jira get"
alias jts="temet-jira search"
alias jtm="temet-jira export --assignee me"
alias jte="temet-jira export"

# Functions for common tasks
jt-mine() {
  temet-jira export --assignee "me" --status "In Progress"
}

jt-review() {
  temet-jira export --status Review
}

jt-bugs() {
  temet-jira export --type Bug --priority High
}
```

Then use:
```bash
jt-mine       # Your active work
jt-review     # Items in review
jt-bugs       # High priority bugs
```

### Data Backup

**Regular backups:**
```bash
#!/bin/bash
# backup_jira.sh
DATE=$(date +%Y%m%d)
PROJECT="PROJ"

# Full backup with history
temet-jira export --project "$PROJECT" --all --expand changelog \
  --format jsonl -o "backup_${PROJECT}_${DATE}.jsonl"

echo "Backup complete: backup_${PROJECT}_${DATE}.jsonl"
```

**Incremental backups:**
```bash
# Daily - get only updated issues
temet-jira search "project = PROJ AND updated >= -1d" \
  --expand changelog --format jsonl -o "incremental_$(date +%Y%m%d).jsonl"
```

## Related Documentation

- [CLI Reference](../reference/cli_reference.md) - Complete command reference
- [Python API Guide](python_api_guide.md) - Using the Python API
- [Setup Guide](jira_setup.md) - Initial configuration
- [ADF Reference](../reference/adf_reference_guide.md) - Document formatting
