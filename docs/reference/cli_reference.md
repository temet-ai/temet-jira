# CLI Command Reference

Complete reference for all `temet-jira` CLI commands.

## Table of Contents

- [Global Options](#global-options)
- [Commands](#commands)
  - [get](#get)
  - [search](#search)
  - [create](#create)
  - [update](#update)
  - [comment](#comment)
  - [transitions](#transitions)
  - [epics](#epics)
  - [epic-details](#epic-details)
  - [export](#export)
  - [analyze state-durations](#analyze-state-durations)
  - [setup](#setup)
  - [types](#types)
  - [mcp](#mcp)
- [Output Formats](#output-formats)

## Global Options

All commands support these options:

- `--help` - Show help message and exit
- `--format {table,json,csv,jsonl}` - Output format (where applicable)
- `-o, --output FILE` - Write output to file instead of stdout

## Commands

### get

Get full details of a specific Jira issue.

**Usage:**
```bash
temet-jira get ISSUE_KEY [OPTIONS]
```

**Arguments:**
- `ISSUE_KEY` - The issue key (e.g., PROJ-123)

**Options:**
- `--format {table,json,jsonl,csv}` - Output format (default: table)
- `-o, --output FILE` - Write output to file
- `--expand TEXT` - Expand additional fields (comma-separated: changelog, transitions)
- `--comments` - Fetch and display comments
- `--fields {standard,all}` - Field set to display (default: standard)

**Examples:**
```bash
# Get basic issue details
temet-jira get PROJ-123

# Export single issue as CSV
temet-jira get PROJ-123 --format csv -o issue.csv

# Export as JSON
temet-jira get PROJ-123 --format json -o issue.json

# Get issue with changelog
temet-jira get PROJ-123 --expand changelog

# Get all fields including custom
temet-jira get PROJ-123 --fields all
```

---

### search

Search for issues using JQL (Jira Query Language).

**Usage:**
```bash
temet-jira search JQL_QUERY [OPTIONS]
```

**Arguments:**
- `JQL_QUERY` - Jira Query Language search string

**Options:**
- `--fields TEXT` - Comma-separated list of fields to include
- `--expand TEXT` - Expand additional fields (changelog, transitions)
- `--max-results INTEGER` - Maximum number of results (default: 50)
- `--all` - Retrieve all results (no limit)
- `--format {table,json,csv,jsonl}` - Output format
- `-o, --output FILE` - Write to file

**Examples:**
```bash
# Basic search
temet-jira search "project = PROJ AND status = 'In Progress'"

# Search with custom fields
temet-jira search "assignee = currentUser()" --fields summary,status,priority

# Get all results as JSON
temet-jira search "project = PROJ" --all --format json -o all_issues.json

# Search with changelog for analysis
temet-jira search "project = PROJ" --expand changelog --format json

# Complex JQL query
temet-jira search "project = PROJ AND (status = 'In Progress' OR status = 'Review') AND priority = High"
```

---

### create

Create a new Jira issue.

**Usage:**
```bash
temet-jira create [OPTIONS]
```

**Options:**
- `--summary TEXT` - Issue summary/title (required)
- `--type TEXT` - Issue type (Task, Bug, Story, Epic, etc.)
- `--project TEXT` - Project key (defaults to JIRA_DEFAULT_PROJECT)
- `--description TEXT` - Issue description
- `--priority TEXT` - Priority (Highest, High, Medium, Low, Lowest)
- `--assignee TEXT` - Assignee email or username
- `--labels TEXT` - Comma-separated labels
- `--epic TEXT` - Epic key to link to
- `--component TEXT` - Component name

**Examples:**
```bash
# Simple task
temet-jira create --summary "Fix login bug" --type Task

# Full issue with details
temet-jira create \
  --summary "Implement OAuth2" \
  --type Story \
  --description "Add OAuth2 authentication" \
  --priority High \
  --labels "backend,security" \
  --epic PROJ-100

# Create in specific project
temet-jira create --summary "Update docs" --type Task --project DOCS
```

---

### update

Update an existing Jira issue.

**Usage:**
```bash
temet-jira update ISSUE_KEY [OPTIONS]
```

**Arguments:**
- `ISSUE_KEY` - The issue key to update

**Options:**
- `--summary TEXT` - New summary/title
- `--description TEXT` - New description
- `--priority TEXT` - New priority
- `--assignee TEXT` - New assignee
- `--status TEXT` - Transition to new status
- `--labels TEXT` - New labels (replaces existing)

**Examples:**
```bash
# Update status
temet-jira update PROJ-123 --status "In Progress"

# Update multiple fields
temet-jira update PROJ-123 \
  --summary "Updated title" \
  --priority High \
  --assignee user@example.com

# Update description
temet-jira update PROJ-123 --description "New detailed description"

# Update labels
temet-jira update PROJ-123 --labels "urgent,backend,security"
```

---

### comment

Add a comment to a Jira issue.

**Usage:**
```bash
temet-jira comment ISSUE_KEY [OPTIONS]
```

**Arguments:**
- `ISSUE_KEY` - The issue key to comment on

**Options:**
- `-m, --message TEXT` - Comment text (if not provided, will prompt)

**Examples:**
```bash
# Add comment with flag
temet-jira comment PROJ-123 -m "This looks good to merge"

# Interactive mode (will prompt for comment)
temet-jira comment PROJ-123
```

---

### transitions

Show available workflow transitions for an issue.

**Usage:**
```bash
temet-jira transitions ISSUE_KEY
```

**Arguments:**
- `ISSUE_KEY` - The issue key

**Examples:**
```bash
# View available transitions
temet-jira transitions PROJ-123
```

**Output:**
Lists all possible state transitions from the current state (e.g., "In Progress", "Done", "Review").

---

### epics

List all epics in a project.

**Usage:**
```bash
temet-jira epics [OPTIONS]
```

**Options:**
- `--project TEXT` - Project key (defaults to JIRA_DEFAULT_PROJECT)
- `--format {table,json,csv,jsonl}` - Output format
- `-o, --output FILE` - Write to file

**Examples:**
```bash
# List epics (uses default project)
temet-jira epics

# List epics for specific project
temet-jira epics --project PROJ

# Export as JSON
temet-jira epics --project PROJ --format json -o epics.json
```

---

### epic-details

Get detailed information about an epic, optionally including child issues.

**Usage:**
```bash
temet-jira epic-details EPIC_KEY [OPTIONS]
```

**Arguments:**
- `EPIC_KEY` - The epic key

**Options:**
- `--show-children` - Include child issues in output
- `--format {table,json,csv,jsonl}` - Output format
- `-o, --output FILE` - Write to file

**Examples:**
```bash
# Get epic details only
temet-jira epic-details PROJ-100

# Get epic with all child issues
temet-jira epic-details PROJ-100 --show-children

# Export epic and children as JSON
temet-jira epic-details PROJ-100 --show-children --format json -o epic.json
```

---

### export

Export issues with advanced filtering and formatting options.

**Usage:**
```bash
temet-jira export [OPTIONS]
```

**Options:**

**Project & Search:**
- `--project TEXT` - Project key (defaults to JIRA_DEFAULT_PROJECT)
- `--jql TEXT` - Custom JQL query (overrides other filters)

**Filters:**
- `--status TEXT` - Filter by status
- `--assignee TEXT` - Filter by assignee (use "me" for current user)
- `--priority TEXT` - Filter by priority
- `--type TEXT` - Filter by issue type
- `--component TEXT` - Filter by component
- `--created TEXT` - Filter by creation date (e.g., "-7d", "today", "2024-01-01")

**Output:**
- `--format {table,json,csv,jsonl}` - Output format
- `-o, --output FILE` - Write to file
- `--all` - Export all results (no limit)
- `--max-results INTEGER` - Limit number of results

**Grouping & Stats:**
- `--group-by {assignee,status,priority}` - Group results
- `--stats` - Display statistics

**Advanced:**
- `--expand TEXT` - Expand fields (changelog, transitions)
- `--fields TEXT` - Specific fields to include

**Examples:**
```bash
# Export all issues (uses default project)
temet-jira export --format csv -o tickets.csv

# Export specific project
temet-jira export --project PROJ --format json -o proj_issues.json

# Filter by status
temet-jira export --status "In Progress" --format table

# Filter by assignee
temet-jira export --assignee "me" --format csv -o my_tickets.csv

# Multiple filters
temet-jira export \
  --project PROJ \
  --status "In Progress" \
  --assignee "me" \
  --priority High \
  --format csv -o filtered.csv

# Group results
temet-jira export --group-by assignee --stats

# Export with changelog for analysis
temet-jira export --project PROJ --expand changelog --format json -o analysis.json

# Export recent issues
temet-jira export --created "-7d" --format table

# Export all issues (large dataset)
temet-jira export --project PROJ --all --format jsonl -o all_issues.jsonl

# Custom JQL
temet-jira export --jql "assignee = currentUser() AND status NOT IN (Done, Closed)"
```

---

### analyze state-durations

Analyze how long issues spent in each workflow state.

**Usage:**
```bash
temet-jira analyze state-durations INPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE` - JSON file with issues (must include changelog)

**Options:**
- `--format {csv,json,jsonl,table}` - Output format (default: from config, falls back to table)
- `-o, --output FILE` - Write output to file (prints to console if omitted)
- `--date-from YYYY-MM-DD` - Filter issues created on or after this date
- `--date-to YYYY-MM-DD` - Filter issues created on or before this date
- `--business-hours` - Calculate durations in business hours (9 AM–5 PM, weekdays)
- `--timezone TEXT` - Timezone for business hours calculation (default: UTC)

**Prerequisites:**
Issues must be exported with `--expand changelog`:
```bash
temet-jira export --project PROJ --expand changelog --format json -o issues.json
```

**Examples:**
```bash
# Analyze and save as CSV
temet-jira analyze state-durations issues.json -o durations.csv

# View as table in terminal
temet-jira analyze state-durations issues.json --format table

# Export as JSON for further processing
temet-jira analyze state-durations issues.json --format json -o durations.json

# Filter by date range
temet-jira analyze state-durations issues.json --date-from 2025-01-01 --date-to 2025-03-31 -o q1.csv

# Business hours only
temet-jira analyze state-durations issues.json --business-hours --timezone "Europe/London" -o durations.csv
```

---

### setup

Interactive configuration wizard. Guides you through setting up your Jira credentials and saves them to `~/.config/temet-jira/config.yaml`.

**Usage:**
```bash
temet-jira setup
```

---

### types

List available issue types for a project.

**Usage:**
```bash
temet-jira types [OPTIONS]
```

**Options:**
- `--project TEXT` - Project key (defaults to JIRA_DEFAULT_PROJECT)

---

### mcp

Manage MCP server configuration.

**Subcommands:**
- `temet-jira mcp add` — Interactive setup: scans for existing config files and prints the correct JSON snippet for your MCP client (Claude Code, Cursor, Windsurf, VS Code, Zed)
- `temet-jira mcp tools` — List all tools exposed by the MCP server

---

## Output Formats

All commands that produce output (`get`, `search`, `epics`, `epic-details`, `export`, `analyze state-durations`) support the same four formats:

| Format | Best For | File Extension |
|--------|----------|----------------|
| **table** | Console viewing | N/A (stdout only) |
| **json** | Readability, small datasets | `.json` |
| **csv** | Spreadsheets, Excel | `.csv` |
| **jsonl** | Large datasets, streaming | `.jsonl` |

### Format Details

**table**
- Human-readable console output
- Formatted with Rich library
- Cannot be written to file (use `--format json/csv/jsonl` with `-o`)

**json**
- Pretty-printed JSON
- Easy to read and parse
- Best for small to medium datasets
- One JSON array with all results

**csv**
- Comma-separated values
- Compatible with Excel, Google Sheets
- Flattens nested structures
- Good for data analysis

**jsonl**
- JSON Lines format (one JSON object per line)
- Most efficient for large datasets
- Supports streaming processing
- Recommended for exports with 100+ issues

### Setting a Default Format

To avoid typing `--format` every time, set your preferred default:

```bash
temet-jira config set default_format json
```

Or via environment variable:
```bash
export JIRA_DEFAULT_FORMAT=json
```

### Choosing a Format

```bash
# Console viewing - use table (default)
temet-jira search "project = PROJ"

# Small dataset for analysis - use JSON
temet-jira export --project PROJ --format json -o issues.json

# Spreadsheet import - use CSV
temet-jira export --project PROJ --format csv -o issues.csv

# Large dataset (100+ issues) - use JSONL
temet-jira export --project PROJ --all --format jsonl -o all_issues.jsonl
```

---

## Environment Variables

See [Setup Guide](../guides/jira_setup.md) for complete configuration details.

**Required:**
- `JIRA_BASE_URL` - Your Jira instance URL
- `JIRA_USERNAME` - Your email address
- `JIRA_API_TOKEN` - API token from Jira

**Optional:**
- `JIRA_DEFAULT_PROJECT` - Default project key
- `JIRA_DEFAULT_COMPONENT` - Default component filter
- `JIRA_DEFAULT_FORMAT` - Default output format: `table`, `json`, `jsonl`, `csv` (default: `table`)
- `JIRA_DEFAULT_MAX_RESULTS` - Default max results per query (default: 300)
- `JIRA_REQUEST_TIMEOUT` - Request timeout (seconds)
- `JIRA_MAX_RETRIES` - Maximum retry attempts

All optional settings can also be managed via the config file:

```bash
temet-jira config set default_format json     # set default output format
temet-jira config set project PROJ            # set default project
temet-jira config set max_results 100         # set default max results
temet-jira config set component "Backend"     # set default component filter
```

---

## JQL (Jira Query Language) Reference

Quick reference for common JQL patterns:

### Basic Syntax
```bash
# Simple equality
project = PROJ

# AND operator
project = PROJ AND status = Open

# OR operator
status = 'In Progress' OR status = Review

# NOT operator
status != Done

# IN operator
status IN ('In Progress', Review, Testing)

# NOT IN operator
priority NOT IN (Low, Lowest)
```

### Common Filters
```bash
# Current user
assignee = currentUser()

# Date ranges
created >= 2024-01-01 AND created <= 2024-01-31
updated >= -7d

# Empty/null fields
assignee is EMPTY
assignee is not EMPTY

# Text search
summary ~ "authentication"
description ~ "bug"

# Labels
labels = urgent
labels in (backend, frontend)
```

### Functions
```bash
# Current user's issues
assignee = currentUser()

# Recent updates
updated >= startOfWeek()
created >= startOfMonth()

# Members of a group
assignee in membersOf("developers")

# Issues in active sprints
sprint in openSprints()
```

### Examples
```bash
# Active issues assigned to me
temet-jira search "assignee = currentUser() AND status NOT IN (Done, Closed)"

# High priority bugs
temet-jira search "project = PROJ AND type = Bug AND priority = High"

# Recent issues
temet-jira search "project = PROJ AND created >= -7d"

# Unassigned tasks
temet-jira search "project = PROJ AND assignee is EMPTY AND type = Task"

# Issues in specific sprint
temet-jira search "project = PROJ AND sprint = 'Sprint 10'"
```

---

## Common Patterns

### Get Your Active Work
```bash
temet-jira export --assignee "me" --status "In Progress"
```

### Find High Priority Items
```bash
temet-jira export --priority High --status "To Do"
```

### Workflow Analysis
```bash
# 1. Export with changelog
temet-jira export --project PROJ --expand changelog --format json -o issues.json

# 2. Analyze state durations
temet-jira analyze state-durations issues.json -o durations.csv
```

### Generate Reports
```bash
# Issues by assignee
temet-jira export --group-by assignee --stats

# Export for spreadsheet
temet-jira export --project PROJ --all --format csv -o report.csv
```

### Bulk Operations
```bash
# 1. Find issues to update
temet-jira export --status "In Progress" --format json -o to_update.json

# 2. Update each one
temet-jira update PROJ-123 --status "Review"
temet-jira update PROJ-124 --status "Review"
```

---

For more examples and use cases, see the [Usage Guide](../guides/usage_guide.md).
