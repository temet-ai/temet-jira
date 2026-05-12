# Jira Slash Commands Reference

Comprehensive guide to all available Jira slash commands for this project.

## Quick Reference

### View & Query Commands
- `/jira:get <issue-key>` - View detailed issue information
- `/jira:search <jql-query>` - Search issues using JQL
- `/jira:my-tickets` - Show your active assigned tickets
- `/jira:transitions <issue-key>` - Show available workflow transitions
- `/jira:epics [project]` - List all epics in a project
- `/jira:epic-details <epic-key>` - View epic with child issues
- `/jira:export <project>` - Export issues with filtering and formatting

### Workflow Commands

### Create & Modify Commands
- `/jira:create <summary>` - Create a basic issue (CLI-based)
- `/jira:create-ticket <summary>` - Create issue with agent assistance (recommended)
- `/jira:create-epic <summary>` - Create a new epic with structure
- `/jira:update <issue-key>` - Update issue fields or status
- `/jira:comment <issue-key> <text>` - Add comment to issue
- `/jira:enrich-epic <epic-key>` - Add structure to existing epic
- `/jira:batch-create <epic-key>` - Create multiple issues from requirements

### Analysis Commands
- `/jira:analyze-states <input-file>` - Analyze state durations from JSON export

---

## Command Details

### View & Query Commands

#### `/jira:get <issue-key>`
**Description**: Get detailed information about a specific issue

**Usage**:
```
/jira:get PROJ-123
/jira:get PROJ-456
```

**Shows**: Full issue details including summary, status, assignee, description, labels, timestamps

---

#### `/jira:search <jql-query>`
**Description**: Search for issues using JQL (Jira Query Language)

**Usage**:
```
/jira:search "project = PROJ AND status = Open"
/jira:search "assignee = currentUser() AND priority = High"
/jira:search "parent = PROJ-100"
```

**Common JQL Patterns**:
- By project: `project = PROJ`
- By status: `status IN ('To Do', 'In Progress')`
- By assignee: `assignee = currentUser()`
- Date range: `created >= 2024-01-01 AND created <= 2024-12-31`
- By epic: `parent = PROJ-100`
- By label: `labels = authentication`

**Output Formats**: table (default), json, csv, jsonl

---

#### `/jira:my-tickets`
**Description**: Show all your active assigned tickets

**Usage**:
```
/jira:my-tickets
```

**Shows**: All active tickets assigned to you, grouped by status
**Excludes**: Done, Closed, Cancelled tickets

---

#### `/jira:transitions <issue-key>`
**Description**: Show available workflow transitions for an issue

**Usage**:
```
/jira:transitions PROJ-123
```

**Shows**: List of available status transitions (e.g., "In Progress", "Done", "Blocked")
**Use Case**: Check what statuses an issue can move to before updating

---

#### `/jira:epics [project]`
**Description**: List all epics in a project

**Usage**:
```
/jira:epics                    # Uses JIRA_DEFAULT_PROJECT
/jira:epics PROJ              # List PROJ epics
/jira:epics PROJ --max-results 50
```

**Shows**: Table of epics with keys, summaries, statuses, and dates

---

### Workflow Commands

**Description**: Complete workflow to start working on a Jira ticket

**Usage**:
```
```

**What it does**:
1. Fetches ticket details from Jira
2. Creates workspace at `artifacts/<TICKET_KEY>/`
3. Determines target repository from ticket's Component field
4. Checks repository git state (must be on clean main)
5. Pulls latest code and creates feature branch using `cb` command
6. Analyzes codebase against ticket requirements
7. Creates detailed implementation plan in `planning.md`
8. Creates todo list with file-by-file tasks
9. Asks user to review before proceeding

**Repository Mapping** (via Component field):
- `your-service` → `repositories/your-repo/your-service`
- `your-catalog-service` → `repositories/wtr-supplier-product/your-catalog-service`
- `your-config-service` → `repositories/your-repo/your-config-service`

**Branch naming**: `ddt/PROJ-<number>-<topic>` (via `cb` command)

**Best For**: Starting fresh work on a ticket with full planning workflow

---

#### `/jira:epic-details <epic-key> [--show-children]`
**Description**: Get detailed epic information including child issues

**Usage**:
```
/jira:epic-details PROJ-100
/jira:epic-details PROJ-50 --show-children
```

**Shows**:
- Epic details (summary, status, description)
- Child issues table (with --show-children flag)
- Total child count

---

#### `/jira:export <project> [filters]`
**Description**: Export issues with flexible filtering and formatting

**Usage**:
```
# Export to CSV
/jira:export PROJ --format csv -o tickets.csv

# Export with filters
/jira:export PROJ --status "In Progress" --priority High --format json -o filtered.json

# Export all tickets to JSONL
/jira:export PROJ --all --format jsonl -o all_tickets.jsonl

# Export with statistics
/jira:export PROJ --stats --group-by status

# Custom JQL
/jira:export PROJ --jql "created >= -30d" --format csv -o recent.csv
```

**Formats**: table, json, jsonl, csv

**Filters**:
- `--status` - Filter by status
- `--assignee` - Filter by assignee (me, unassigned, or name)
- `--priority` - Filter by priority
- `--type` - Filter by issue type
- `--created` - Filter by creation date
- `--jql` - Custom JQL query

**Options**:
- `--stats` - Show summary statistics
- `--group-by` - Group by status/assignee/priority
- `--expand` - Include expanded fields (e.g., changelog)
- `--all` - Fetch all results (bypasses limit)
- `--limit` - Limit number of results (default: 100)

---

### Create & Modify Commands

#### `/jira:create <summary> [options]`
**Description**: Create a basic issue using CLI directly

**Usage**:
```
/jira:create --summary "Update documentation"
/jira:create --summary "Fix login bug" --type "Bug" --priority "High"
/jira:create --summary "User story" --type "Story" --epic "PROJ-100"
```

**Options**:
- `--summary, -s` (required) - Issue title
- `--description, -d` - Issue description
- `--type, -t` - Issue type (Task, Story, Bug)
- `--epic, -e` - Epic key to link to
- `--priority, -p` - Priority level
- `--labels, -l` - Comma-separated labels
- `--project` - Project key (uses JIRA_DEFAULT_PROJECT if not set)

**Best For**: Simple, straightforward issues
**For Complex Issues**: Use `/jira:create-ticket` instead

---

#### `/jira:create-ticket <summary> [epic-key]`
**Description**: Create issue with agent assistance for proper formatting

**Usage**:
```
/jira:create-ticket "Implement OAuth2 authentication"
/jira:create-ticket "Add user profile endpoint" PROJ-100
```

**Agent Features**:
- Structured description using ADF (Atlassian Document Format)
- Automatic labeling based on content
- Appropriate issue type selection
- Comprehensive acceptance criteria
- Epic linking

**Best For**: Complex issues requiring detailed descriptions and structure

---

#### `/jira:create-epic <summary>`
**Description**: Create a new epic with structure

**Usage**:
```
/jira:create-epic "Authentication System Overhaul"
```

**Agent Features**:
- Epic structure with goals and scope
- Breakdown into suggested child issues
- Proper epic field configuration
- Acceptance criteria

---

#### `/jira:update <issue-key> [fields]`
**Description**: Update issue fields or transition status

**Usage**:
```
# Update summary
/jira:update PROJ-123 --summary "New summary"

# Update status
/jira:update PROJ-123 --status "In Progress"

# Update assignee
/jira:update PROJ-123 --assignee "<account-id>"

# Update priority and labels
/jira:update PROJ-123 --priority "High" --labels "urgent,backend"

# Update description
/jira:update PROJ-123 --description "Updated description text"
```

**Options**:
- `--summary` - Update issue summary
- `--description` - Update description
- `--assignee` - Update assignee (account ID or email)
- `--priority` - Update priority
- `--labels` - Update labels (comma-separated)
- `--status` - Transition to new status

---

#### `/jira:comment <issue-key> <message>`
**Description**: Add a comment to an issue

**Usage**:
```
/jira:comment PROJ-123 "This looks good, approving"
/jira:comment PROJ-456 "Fixed in commit abc123"
```

---

#### `/jira:enrich-epic <epic-key>`
**Description**: Add structure to an existing epic

**Usage**:
```
/jira:enrich-epic PROJ-100
```

**Agent Features**:
- Analyzes existing epic
- Adds comprehensive description
- Suggests breakdown structure
- Updates epic fields

---

#### `/jira:batch-create <epic-key> <requirements>`
**Description**: Create multiple issues from a requirements list

**Usage**:
```
/jira:batch-create PROJ-100 "1. Implement login, 2. Add logout, 3. Session management"
```

**Agent Features**:
- Parses requirements list
- Creates individual tickets
- Links all to specified epic
- Maintains consistent structure

---

### Analysis Commands

#### `/jira:analyze-states <input-file> [options]`
**Description**: Analyze state durations from exported JSON

**Usage**:
```
# Basic analysis
/jira:analyze-states issues.json -o durations.csv

# With date filters
/jira:analyze-states issues.json -o durations.csv --date-from 2024-01-01 --date-to 2024-12-31

# With business hours calculation
/jira:analyze-states issues.json -o durations.csv --business-hours --timezone "America/New_York"
```

**Options**:
- `-o, --output` (required) - Output CSV file path
- `--date-from` - Start date filter (YYYY-MM-DD)
- `--date-to` - End date filter (YYYY-MM-DD)
- `--business-hours` - Calculate using business hours only
- `--timezone` - Timezone for calculations (default: UTC)

**Workflow**:
1. Export issues with changelog: `/jira:export PROJ --expand changelog --format json -o issues.json`
2. Analyze state durations: `/jira:analyze-states issues.json -o durations.csv`
3. Open CSV to review time spent in each status

---

## Environment Configuration

Set these in your `.env` file:

```bash
# Required
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Optional
JIRA_DEFAULT_PROJECT=YOUR_PROJECT
```

## Getting Help

- Run any CLI command with `--help` for detailed options
- Check `CLAUDE.md` for project-specific guidance
- See `docs/reference/` for detailed documentation

---

## Command Cheat Sheet

| Task | Command |
|------|---------|
| View issue | `/jira:get PROJ-123` |
| My tickets | `/jira:my-tickets` |
| Search | `/jira:search "project = PROJ"` |
| Create simple issue | `/jira:create --summary "Fix bug"` |
| Create complex issue | `/jira:create-ticket "Feature description"` |
| Update status | `/jira:update PROJ-123 --status "Done"` |
| Add comment | `/jira:comment PROJ-123 "Completed"` |
| List epics | `/jira:epics PROJ` |
| View epic | `/jira:epic-details PROJ-100 --show-children` |
| Export to CSV | `/jira:export PROJ --format csv -o data.csv` |
| Analyze workflow | `/jira:analyze-states issues.json -o analysis.csv` |

---

## Tips & Best Practices

1. **Use tab completion**: Type `/jira:` and press tab to see all commands
2. **Check transitions first**: Use `/jira:transitions` before updating status
3. **Export before analysis**: Always export with `--expand changelog` for state analysis
4. **Use JSONL for large exports**: More efficient for streaming and processing
5. **Set default project**: Add `JIRA_DEFAULT_PROJECT` to `.env` for convenience
6. **Combine filters**: Use multiple filters with export for precise results
7. **Save to files**: Use `--output` or `-o` with json/csv/jsonl formats
8. **Use agent commands for complex tasks**: `/jira:create-ticket`, `/jira:create-epic`, etc.
9. **Use CLI commands for simple tasks**: `/jira:create`, `/jira:get`, etc.
