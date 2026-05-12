# When to Use Which Jira Tool

## Decision Tree

```
Need to interact with Jira?
│
├─ Single operation (get/search/create/update)?
│  └─→ Use temet-jira CLI (FASTEST, PREFERRED)
│
├─ Batch operations (multiple tickets)?
│  ├─ Simple loop (create 5 related stories)?
│  │  └─→ Shell script with temet-jira CLI
│  │
│  └─ Complex analysis (dependency graphs, reports)?
│     └─→ jira-ticket-manager agent
│
└─ Low-level API operation not in temet-jira?
   └─→ curl + Jira REST API (LAST RESORT)
```

## Available Jira Tools (in priority order)

### 1. temet-jira CLI ⭐ PREFERRED

**When to use:**
- Getting ticket details
- Searching for tickets
- Creating tickets with formatted descriptions
- Exporting ticket data
- Listing epics and their children
- Adding comments
- Updating ticket fields
- Viewing transitions

**Examples:**
```bash
temet-jira get PROJ-123
temet-jira search 'project=PROJ AND text~"export"'
temet-jira epics --project PROJ
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl
temet-jira create --project PROJ --type Story --summary "Title"
temet-jira comment PROJ-123 "Update message"
temet-jira update PROJ-123 --status "In Progress"
```

**Advantages:**
- Already installed and configured
- Rich formatting (tables, colored output)
- Handles authentication automatically
- Professional description formatting (ADF)
- Supports JSON/JSONL/CSV export
- Fast and reliable
- Stable interface

**Limitations:**
- Single operation at a time
- No complex analysis features
- Limited to supported commands

**How to check if available:**
```bash
temet-jira --version
```

---

### 2. Shell Scripts with temet-jira CLI

**When to use:**
- Creating multiple related tickets
- Batch operations (10-50 tickets)
- Conditional logic based on ticket data
- Data transformation pipelines

**Example:**
```bash
#!/bin/bash
# Create epic with stories

EPIC=$(temet-jira create --project PROJ --type Epic \
  --summary "Q1 Features" --format json | jq -r '.key')

for feature in "Auth" "API" "Dashboard"; do
  temet-jira create --project PROJ --type Story \
    --summary "$feature" --parent "$EPIC"
done
```

**Advantages:**
- Uses familiar shell scripting
- Combines temet-jira with other CLI tools (jq, awk, grep)
- Scriptable and repeatable
- Version controllable

**Limitations:**
- No built-in error handling for Jira-specific issues
- Manual retry logic needed
- Limited analysis capabilities

---

### 3. jira-ticket-manager Agent

**When to use:**
- Complex multi-ticket operations (batch create, enrich epics)
- Ticket analysis and reporting
- State duration analysis
- Dependency management
- When you need autonomous ticket management
- Operations requiring decision-making

**How to invoke:**
Via Claude Code Task tool:
```
User: "Analyze PROJ project and create summary report"
Assistant: [Invokes jira-ticket-manager agent]
```

**Agent capabilities:**
- Multi-step ticket workflows
- Intelligent error handling
- Complex state transition analysis
- Dependency graph creation
- Batch enrichment of descriptions
- Custom data transformations
- Analysis and reporting

**Advantages:**
- Specialized for complex Jira workflows
- Can perform multi-step operations
- Built-in error handling and retry logic
- Decision-making capabilities
- Can use temet-jira CLI internally

**Limitations:**
- Requires Claude Code environment
- More overhead than direct CLI
- Agent invocation adds latency

**When NOT to use:**
- Simple get/search operations (use temet-jira CLI)
- Single ticket creation (use temet-jira CLI)
- Standard exports (use temet-jira CLI)

---

### 4. curl + Jira REST API ⚠️ LAST RESORT

**When to use:**
- temet-jira doesn't support the operation
- Need low-level API access for debugging
- Testing authentication issues
- Accessing undocumented Jira features

**Example:**
```bash
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123"
```

**Issues:**
- Environment variable handling is fragile
- No automatic formatting
- More error-prone
- Requires manual JSON parsing
- No ADF formatting helpers
- Authentication errors harder to debug

**Before using curl, ask yourself:**
1. Does temet-jira support this operation? (Check: `temet-jira --help`)
2. Can jira-ticket-manager agent handle this?
3. Is this truly a low-level API need?

**Common mistakes:**
```bash
# ❌ BAD: Using curl when temet-jira works
curl "$JIRA_BASE_URL/rest/api/3/search?jql=project=PROJ"

# ✅ GOOD: Use temet-jira instead
temet-jira search 'project=PROJ'
```

---

## Decision Matrix

| Operation | Use This | Not This |
|-----------|----------|----------|
| Get single ticket | `temet-jira get` | curl, agent |
| Search tickets | `temet-jira search` | curl, agent |
| Create 1 ticket | `temet-jira create` | agent, curl |
| Create 5 related tickets | Shell script + temet-jira | agent, curl |
| Create 100+ tickets with logic | jira-ticket-manager agent | shell script, curl |
| Export for analysis | `temet-jira export --format jsonl` | curl, manual queries |
| State duration analysis | `temet-jira analyze state-durations` | agent, manual |
| Dependency graph | jira-ticket-manager agent | temet-jira, curl |
| List epics | `temet-jira epics` | search, curl |
| Add comment | `temet-jira comment` | curl, agent |
| Update status | `temet-jira update --status` | curl, transitions + curl |
| Undocumented API feature | curl | temet-jira, agent |

## Common Scenarios

### Scenario 1: "Get details of PROJ-370"
**Use:** `temet-jira get PROJ-370`

**Why:** Single operation, direct CLI is fastest and most reliable.

**Don't use:** curl (fragile), agent (overkill)

---

### Scenario 2: "Search for tickets about export"
**Use:** `temet-jira search 'project=PROJ AND text~"export"'`

**Why:** Built-in JQL support, formatted output.

**Don't use:** curl + manual JQL (error-prone), agent (unnecessary)

---

### Scenario 3: "Create epic with 10 stories"
**Use:** Shell script with temet-jira CLI in loop

```bash
EPIC=$(temet-jira create --type Epic --summary "Title" --format json | jq -r '.key')
for i in {1..10}; do
  temet-jira create --type Story --summary "Story $i" --parent "$EPIC"
done
```

**Why:** Straightforward batch operation, no complex logic needed.

**Don't use:** agent (overkill), curl (too much code)

---

### Scenario 4: "Analyze project and create dependency report"
**Use:** jira-ticket-manager agent

**Why:** Complex analysis, multi-step workflow, decision-making required.

**Don't use:** temet-jira alone (no analysis features), curl (too manual)

---

### Scenario 5: "Export all tickets to CSV for spreadsheet"
**Use:** `temet-jira export --project PROJ --all --format csv -o tickets.csv`

**Why:** Built-in CSV formatting, handles pagination.

**Don't use:** curl + manual pagination, agent (unnecessary)

---

### Scenario 6: "Create tickets from CSV file"
**Use:** Shell script reading CSV with temet-jira CLI

```bash
while IFS=, read -r summary description; do
  temet-jira create --project PROJ --type Story \
    --summary "$summary" --description "$description"
done < tickets.csv
```

**Why:** Simple data transformation, CLI handles Jira formatting.

**Don't use:** Pure curl (complex ADF formatting), agent (not needed)

---

### Scenario 7: "Test new Jira beta API endpoint"
**Use:** curl + Jira REST API

**Why:** Endpoint not in temet-jira yet, need low-level access.

**Don't use:** temet-jira (doesn't support it), agent (may not support it)

---

## Red Flags: You're Using the Wrong Tool

### Red Flag 1: "ModuleNotFoundError: No module named 'jira_tool'"
**Problem:** Trying to import jira_tool Python module

**Solution:** Use `temet-jira` CLI instead

```python
# ❌ WRONG
from jira_tool import JiraClient
client = JiraClient()

# ✅ RIGHT
import subprocess
subprocess.run(['temet-jira', 'get', 'PROJ-123'])
```

---

### Red Flag 2: "curl: option : blank argument"
**Problem:** Using curl with environment variables (fragile)

**Solution:** Use `temet-jira` CLI which handles auth automatically

```bash
# ❌ WRONG
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" "$JIRA_BASE_URL/rest/api/3/search"

# ✅ RIGHT
temet-jira search 'project=PROJ'
```

---

### Red Flag 3: Writing manual ADF formatting in shell script
**Problem:** Manually building Atlassian Document Format JSON

**Solution:** Use `temet-jira create` which handles ADF automatically

```bash
# ❌ WRONG (complex ADF JSON)
curl -X POST ... -d '{
  "fields": {
    "description": {
      "type": "doc",
      "version": 1,
      "content": [...]
    }
  }
}'

# ✅ RIGHT (automatic ADF conversion)
temet-jira create --project PROJ --type Story \
  --summary "Title" --description "Simple text converts to ADF"
```

---

### Red Flag 4: Invoking agent for simple get/search
**Problem:** Using jira-ticket-manager agent for single-ticket operations

**Solution:** Use `temet-jira` CLI directly (faster, simpler)

```bash
# ❌ WRONG (overkill)
Task: "Get details of PROJ-370"
Subagent: jira-ticket-manager

# ✅ RIGHT
temet-jira get PROJ-370
```

---

### Red Flag 5: Manual pagination in curl
**Problem:** Writing loop to handle Jira pagination with curl

**Solution:** Use `temet-jira export --all` (handles pagination)

```bash
# ❌ WRONG (manual pagination)
for ((i=0; i<10; i++)); do
  curl "$JIRA_BASE_URL/rest/api/3/search?startAt=$((i*100))&maxResults=100"
done

# ✅ RIGHT (automatic pagination)
temet-jira export --project PROJ --all --format jsonl -o tickets.jsonl
```

---

## Quick Reference

**Default choice for 90% of operations:**
```bash
temet-jira [command] [options]
```

**Check what's available:**
```bash
temet-jira --help
temet-jira search --help
temet-jira create --help
```

**If temet-jira doesn't support it:**
1. Check if agent can help (complex workflow)
2. Last resort: Use curl (low-level API)

**Never do this:**
```python
from jira_tool import ...  # ❌ Module is private/internal
```

**See Also:**
- Quick reference: `~/.claude/skills/jira-builders/references/QUICK_REFERENCE.md`
- Main skill: `~/.claude/skills/jira-builders/SKILL.md`
- Project docs: `/path/to/temet-jira/CLAUDE.md`
