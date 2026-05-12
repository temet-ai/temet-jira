# Getting Started with temet-jira

Get up and running with temet-jira in 5 minutes.

## 1. Install

Install with uv (recommended):
```bash
uv tool install temet-jira
```

Or with pipx:
```bash
pipx install temet-jira
```

Verify:
```bash
temet-jira --help
```

## 2. Configure

### Option A: Interactive Setup (Recommended)

Run the setup wizard - it will guide you through configuration:

```bash
temet-jira setup
```

The wizard will:
1. Ask for your Jira URL (e.g., `https://company.atlassian.net`)
2. Ask for your email address
3. Ask for your API token (get one at https://id.atlassian.com/manage-profile/security/api-tokens)
4. Optionally set a default project
5. Test the connection
6. Save to `~/.config/temet-jira/config.yaml`

### Option B: Manual Configuration

Set environment variables in `~/.zshrc` or `~/.bashrc`:

```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or create `~/.config/temet-jira/config.yaml` directly:

```yaml
base_url: https://your-company.atlassian.net
username: your-email@example.com
api_token: your-api-token
project: PROJ
```

### Verify Configuration

```bash
# View your config (tokens are masked)
temet-jira config show

# Or just
temet-jira config
```

## 3. Try It Out

```bash
# Get a ticket
temet-jira get PROJ-123

# Search for tickets
temet-jira search "project = PROJ AND status = Open"

# Your active work
temet-jira export --assignee "me" --status "In Progress"

# Export to CSV
temet-jira export --project PROJ --format csv -o tickets.csv

# Create a ticket
temet-jira create --project PROJ --type Task --summary "My new task"
```

## 4. Quick Reference

| Command | What it does |
|---------|--------------|
| `temet-jira setup` | Interactive configuration wizard |
| `temet-jira config` | View current configuration |
| `temet-jira get PROJ-123` | View ticket details |
| `temet-jira search "JQL"` | Search with JQL |
| `temet-jira create --project PROJ --type Task --summary "Title"` | Create ticket |
| `temet-jira update PROJ-123 --status "Done"` | Update ticket |
| `temet-jira comment PROJ-123 "message"` | Add comment |
| `temet-jira export --project PROJ` | Export tickets |
| `temet-jira epics --project PROJ` | List epics |
| `temet-jira transitions PROJ-123` | Show available statuses |

## 5. Configuration Commands

```bash
# View all config
temet-jira config show

# Set a value
temet-jira config set project PROJ

# Get a specific value
temet-jira config get base_url

# Remove a value
temet-jira config unset project

# Show config file path
temet-jira config path

# Edit config file directly
temet-jira config edit
```

## 6. Common Patterns

### Your Daily Work
```bash
# What am I working on?
temet-jira export --assignee "me" --status "In Progress"

# What needs my attention?
temet-jira search "assignee = currentUser() AND status NOT IN (Done, Closed)"
```

### Team Overview
```bash
# All open bugs
temet-jira export --type Bug --jql "resolution = Unresolved"

# Work by assignee
temet-jira export --group-by assignee --stats
```

### Export Data
```bash
# To CSV (for Excel/Sheets)
temet-jira export --project PROJ --format csv -o tickets.csv

# To JSON (for processing)
temet-jira export --project PROJ --format json -o tickets.json

# Large datasets (100+ tickets)
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl
```

### Workflow Analysis
```bash
# Export with history
temet-jira export --project PROJ --expand changelog --format json -o issues.json

# Analyze state durations
temet-jira analyze state-durations issues.json -o durations.csv
```

## 7. JQL Cheat Sheet

```bash
# By status
"status = 'In Progress'"
"status IN (Open, 'To Do', 'In Progress')"
"status NOT IN (Done, Closed)"

# By assignee
"assignee = currentUser()"
"assignee is EMPTY"

# By date
"created >= -7d"            # Last 7 days
"updated >= startOfWeek()"  # This week
"created >= 2024-01-01"     # Since date

# By type/priority
"type = Bug AND priority = High"

# Text search
"summary ~ 'authentication'"

# Combine
"project = PROJ AND status = Open AND assignee = currentUser()"
```

## 8. Claude Code Integration

If you're using Claude Code, you get slash commands:

```
/jira:get PROJ-123              # Get ticket
/jira:search "status = Open"    # Search
/jira:create --project PROJ ... # Create
/jira:export --project PROJ     # Export
/jira:mcp                       # Manage MCP server configuration
```

And skills for AI assistance:
- `jira-api` - API reference
- `jira-builders` - CLI patterns
- `build-jira-document-format` - Advanced ADF document building
- `work-with-adf` - Document formatting

## Next Steps

- **[CLI Reference](../reference/cli_reference.md)** - All commands and options
- **[Usage Guide](usage_guide.md)** - Detailed workflows and examples
- **[Setup Guide](jira_setup.md)** - Advanced configuration
- **[Python API Guide](python_api_guide.md)** - Use in Python scripts

## Troubleshooting

**"Jira URL not configured"** - Run `temet-jira setup` or check your config:
```bash
temet-jira config show
```

**"401 Unauthorized"** - Your API token may be invalid or expired:
- Generate a new token at https://id.atlassian.com/manage-profile/security/api-tokens
- Run `temet-jira setup` to reconfigure

**"404 Not Found"** - Check your base URL:
```bash
temet-jira config get base_url
```

**"403 Forbidden"** - You don't have permission to that project/ticket

---

Questions? Run `temet-jira --help` or check the [full documentation](../../README.md).
