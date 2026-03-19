# Getting Started with jira-tool

Get up and running with jira-tool in 5 minutes.

## 1. Install

```bash
# Clone and install
git clone <repository-url>
cd jira-tool
./scripts/build_and_install.sh

# Verify
jira-tool --help
```

**Alternative (development mode):**
```bash
uv sync
uv run jira-tool --help
```

## 2. Configure

### Option A: Interactive Setup (Recommended)

Run the setup wizard - it will guide you through configuration:

```bash
jira-tool setup
```

The wizard will:
1. Ask for your Jira URL (e.g., `https://company.atlassian.net`)
2. Ask for your email address
3. Ask for your API token (get one at https://id.atlassian.com/manage-profile/security/api-tokens)
4. Optionally set a default project
5. Test the connection
6. Save to `~/.config/jira-tool/config.yaml`

### Option B: Manual Configuration

Set environment variables in `~/.zshrc` or `~/.bashrc`:

```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or create `~/.config/jira-tool/config.yaml` directly:

```yaml
base_url: https://your-company.atlassian.net
username: your-email@example.com
api_token: your-api-token
project: PROJ
```

### Verify Configuration

```bash
# View your config (tokens are masked)
jira-tool config show

# Or just
jira-tool config
```

## 3. Try It Out

```bash
# Get a ticket
jira-tool get PROJ-123

# Search for tickets
jira-tool search "project = PROJ AND status = Open"

# Your active work
jira-tool export --assignee "me" --status "In Progress"

# Export to CSV
jira-tool export --project PROJ --format csv -o tickets.csv

# Create a ticket
jira-tool create --project PROJ --type Task --summary "My new task"
```

## 4. Quick Reference

| Command | What it does |
|---------|--------------|
| `jira-tool setup` | Interactive configuration wizard |
| `jira-tool config` | View current configuration |
| `jira-tool get PROJ-123` | View ticket details |
| `jira-tool search "JQL"` | Search with JQL |
| `jira-tool create --project PROJ --type Task --summary "Title"` | Create ticket |
| `jira-tool update PROJ-123 --status "Done"` | Update ticket |
| `jira-tool comment PROJ-123 "message"` | Add comment |
| `jira-tool export --project PROJ` | Export tickets |
| `jira-tool epics --project PROJ` | List epics |
| `jira-tool transitions PROJ-123` | Show available statuses |

## 5. Configuration Commands

```bash
# View all config
jira-tool config show

# Set a value
jira-tool config set project PROJ

# Get a specific value
jira-tool config get base_url

# Remove a value
jira-tool config unset project

# Show config file path
jira-tool config path

# Edit config file directly
jira-tool config edit
```

## 6. Common Patterns

### Your Daily Work
```bash
# What am I working on?
jira-tool export --assignee "me" --status "In Progress"

# What needs my attention?
jira-tool search "assignee = currentUser() AND status NOT IN (Done, Closed)"
```

### Team Overview
```bash
# All open bugs
jira-tool export --type Bug --jql "resolution = Unresolved"

# Work by assignee
jira-tool export --group-by assignee --stats
```

### Export Data
```bash
# To CSV (for Excel/Sheets)
jira-tool export --project PROJ --format csv -o tickets.csv

# To JSON (for processing)
jira-tool export --project PROJ --format json -o tickets.json

# Large datasets (100+ tickets)
jira-tool export --project PROJ --all --format jsonl -o tickets.jsonl
```

### Workflow Analysis
```bash
# Export with history
jira-tool export --project PROJ --expand changelog --format json -o issues.json

# Analyze state durations
jira-tool analyze state-durations issues.json -o durations.csv
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
/get PROJ-123              # Get ticket
/search "status = Open"    # Search
/create --project PROJ ... # Create
/export --project PROJ     # Export
```

And skills for AI assistance:
- `jira-api` - API reference
- `jira-builders` - CLI patterns
- `work-with-adf` - Document formatting

## Next Steps

- **[CLI Reference](../reference/cli_reference.md)** - All commands and options
- **[Usage Guide](usage_guide.md)** - Detailed workflows and examples
- **[Setup Guide](jira_setup.md)** - Advanced configuration
- **[Python API Guide](python_api_guide.md)** - Use in Python scripts

## Troubleshooting

**"Jira URL not configured"** - Run `jira-tool setup` or check your config:
```bash
jira-tool config show
```

**"401 Unauthorized"** - Your API token may be invalid or expired:
- Generate a new token at https://id.atlassian.com/manage-profile/security/api-tokens
- Run `jira-tool setup` to reconfigure

**"404 Not Found"** - Check your base URL:
```bash
jira-tool config get base_url
```

**"403 Forbidden"** - You don't have permission to that project/ticket

---

Questions? Run `jira-tool --help` or check the [full documentation](../../README.md).
