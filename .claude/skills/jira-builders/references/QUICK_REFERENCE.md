# temet-jira CLI - Quick Reference

## Most Common Operations

### Search & Discovery

```bash
# Get total ticket count
temet-jira search 'project=PROJ' --stats

# Find export-related tickets
temet-jira search 'project=PROJ AND (summary~"export" OR summary~"oracle")'

# List all epics
temet-jira epics --project PROJ

# Get epic with children
temet-jira epic-details PROJ-370

# Search by status
temet-jira search 'project=PROJ AND status="In Progress"'

# Search by assignee
temet-jira search 'project=PROJ AND assignee=currentUser()'

# Complex JQL
temet-jira search 'project=PROJ AND (status="To Do" OR status="In Progress") AND assignee=currentUser() ORDER BY priority DESC'
```

### Export Data for Analysis

```bash
# Export all tickets to JSON Lines (best for processing)
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl

# Then process with jq:
jq -r 'select(.fields.status.name == "To Do") | .key' tickets.jsonl

# Export to CSV for spreadsheets
temet-jira export --project PROJ --all --format csv -o tickets.csv

# Export with changelog (for state analysis)
temet-jira export --project PROJ --expand changelog --format json -o issues.json

# Count tickets by status
jq -r '.fields.status.name' tickets.jsonl | sort | uniq -c
```

### Create Tickets

```bash
# Create epic with formatted description
temet-jira create --project PROJ --type Epic \
  --summary "Daily CSV Export" \
  --description "$(cat <<'EOF'
Epic for CSV export functionality with automated scheduling.

**Goal:** Export project data to CSV daily

**Components:**
- Cloud Scheduler configuration
- Export service implementation
- CSV formatting logic
EOF
)"

# Create story under epic
temet-jira create --project PROJ --type Story \
  --summary "Configure Cloud Scheduler" \
  --parent PROJ-370 \
  --description "Set up Cloud Scheduler to trigger daily at 2 AM UTC"

# Create sub-task
temet-jira create --project PROJ --type Sub-task \
  --summary "Add timezone handling" \
  --parent PROJ-371

# Create with assignee
temet-jira create --project PROJ --type Story \
  --summary "Implement retry logic" \
  --assignee "email@example.com"
```

### Get Ticket Details

```bash
# Rich formatted output (default)
temet-jira get PROJ-370

# JSON output for processing
temet-jira search 'key=PROJ-370' --format json

# Get with specific fields
temet-jira get PROJ-370 --fields summary,status,assignee
```

### Update Tickets

```bash
# Update status
temet-jira update PROJ-370 --status "In Progress"

# Add comment
temet-jira comment PROJ-370 "Started implementation"

# View available transitions
temet-jira transitions PROJ-370
```

## Output Formats

The `--format` flag controls output style:

```bash
# Table (default, for console viewing)
temet-jira search 'project=PROJ' --format table

# JSON (pretty-printed, small datasets)
temet-jira search 'project=PROJ' --format json

# JSONL (one per line, large datasets)
temet-jira export --project PROJ --all --format jsonl -o file.jsonl

# CSV (spreadsheet-compatible)
temet-jira export --project PROJ --all --format csv -o file.csv
```

**Format Selection Guide:**
- **Table**: Console viewing only (not saveable)
- **JSON**: Readability, small-to-medium datasets
- **JSONL**: Large datasets, streaming, line-by-line processing (RECOMMENDED for >100 tickets)
- **CSV**: Spreadsheet analysis, non-technical users

## Common JQL Patterns

```bash
# My open tickets
temet-jira search 'assignee=currentUser() AND status!="Done"'

# Recently updated
temet-jira search 'project=PROJ AND updated >= -7d'

# High priority blockers
temet-jira search 'priority in (Highest, High) AND status="Blocked"'

# Tickets without assignee
temet-jira search 'project=PROJ AND assignee is EMPTY'

# Epics with children
temet-jira search 'project=PROJ AND type=Epic' --expand subtasks

# Text search across summary and description
temet-jira search 'project=PROJ AND text~"authentication"'
```

## Workflow Analysis

State duration analysis requires changelog:

```bash
# Step 1: Export with changelog
temet-jira export PROJ --expand changelog --format json -o issues.json

# Step 2: Analyze durations
temet-jira analyze state-durations issues.json -o durations.csv

# Open in spreadsheet
open durations.csv  # macOS
```

The CSV contains:
- Issue key
- State name
- Start date/time
- End date/time
- Duration (calendar days)
- Business hours (9 AM - 5 PM, weekdays)

## Batch Operations

Create multiple related tickets:

```bash
#!/bin/bash

# Create epic and capture key
EPIC=$(temet-jira create --project PROJ --type Epic \
  --summary "Q1 2026 Features" --format json | jq -r '.key')

# Create stories under epic
for feature in "User Auth" "API Gateway" "Dashboard"; do
  STORY=$(temet-jira create --project PROJ --type Story \
    --summary "$feature" --parent "$EPIC" --format json | jq -r '.key')

  # Create sub-tasks for each story
  for task in "Design" "Implementation" "Testing"; do
    temet-jira create --project PROJ --type Sub-task \
      --summary "$feature - $task" --parent "$STORY"
  done
done

echo "Created epic $EPIC with stories and sub-tasks"
```

## Error Troubleshooting

### "ModuleNotFoundError: No module named 'jira_tool'"

**Cause:** You tried `from jira_tool import ...`

**Solution:** The jira_tool Python module is private/internal. Use `temet-jira` CLI instead.

```bash
# WRONG
python3 -c "from jira_tool import JiraClient"

# RIGHT
temet-jira search 'project=PROJ'
```

### "0 results found" (when tickets exist)

**Debug Steps:**
1. Verify project exists: `temet-jira search 'project=PROJ' --stats`
2. Check JQL syntax with simpler query: `temet-jira search 'key=PROJ-370'`
3. Try without filters: `temet-jira epics --project PROJ`
4. Verify credentials: `echo $JIRA_BASE_URL`

### "temet-jira: command not found"

**Cause:** Tool not installed or not in PATH

**Solution:**
```bash
# Check if installed
which temet-jira

# If not found, install from project directory
cd /path/to/temet-jira
uv sync
uv run temet-jira --version
```

### "Authentication failed" / "401 Unauthorized"

**Debug Steps:**
1. Check environment variables:
   ```bash
   echo $JIRA_BASE_URL
   echo $JIRA_USERNAME
   echo $JIRA_API_TOKEN  # Should show token (careful in shared terminals)
   ```

2. Verify API token is valid:
   - Go to https://id.atlassian.com/manage/api-tokens
   - Check token is active
   - Regenerate if needed

3. Test authentication:
   ```bash
   temet-jira search 'project=PROJ' --stats
   ```

### "curl: option : blank argument"

**Cause:** You tried to use curl with environment variables instead of temet-jira

**Solution:** Use `temet-jira` CLI - it handles authentication automatically

```bash
# WRONG
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" "$JIRA_BASE_URL/rest/api/3/search"

# RIGHT
temet-jira search 'project=PROJ'
```

## Environment Setup

Required environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc
export JIRA_BASE_URL="https://company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token-here"

# Optional: Set defaults
export JIRA_DEFAULT_PROJECT="PROJ"
# export JIRA_DEFAULT_COMPONENT="Your Component"
```

Generate API token:
1. Go to https://id.atlassian.com/manage/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "temet-jira CLI")
4. Copy token and add to environment

## Advanced Tips

### Piping and Filtering

```bash
# Get issue keys only
temet-jira search 'project=PROJ' --format json | jq -r '.issues[].key'

# Count by status
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl
jq -r '.fields.status.name' tickets.jsonl | sort | uniq -c | sort -rn

# Extract custom fields
jq -r '.fields.customfield_10014' tickets.jsonl  # Epic Link
```

### Watch for Changes

```bash
# Monitor ticket status every 30 seconds
watch -n 30 'temet-jira get PROJ-370 --fields status,assignee'
```

### Bulk Export

```bash
# Export multiple projects
for project in PROJ PROJ AUTH; do
  temet-jira export --project $project --all --format jsonl \
    -o "${project}_tickets.jsonl"
done
```

### JSON vs JSONL Performance

For large datasets (>100 tickets), ALWAYS use JSONL:

```bash
# JSON: Loads entire array in memory (slow for 1000+ tickets)
temet-jira export --project PROJ --all --format json -o tickets.json

# JSONL: Streams one ticket per line (fast for any size)
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl

# Process JSONL line-by-line
while IFS= read -r line; do
  echo "$line" | jq -r '.key'
done < tickets.jsonl
```

## When to Use jira-ticket-manager Agent

Use the agent for complex operations that temet-jira CLI doesn't support:

```bash
# Agent invocation (via Claude Code)
Task: "Analyze PROJ project and create summary report with dependencies"
Subagent: jira-ticket-manager
```

**Agent capabilities:**
- Multi-ticket analysis and reporting
- Dependency graph creation
- Batch enrichment of epic descriptions
- Complex state transition analysis
- Custom data transformations

**CLI capabilities (use first):**
- Single ticket operations
- Standard searches
- Basic exports
- Epic listing
- Comment management

## See Also

- Main skill documentation: `~/.claude/skills/jira-builders/SKILL.md`
- Project CLAUDE.md: `/path/to/temet-jira/CLAUDE.md`
- Tool selection guide: `~/.claude/skills/jira-builders/references/TOOL_SELECTION.md`
