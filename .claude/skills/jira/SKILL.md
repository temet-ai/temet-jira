---
name: jira
description: Manages all Jira ticket operations including searching, creating, updating, analyzing, and exporting issues. Use when you need to search tickets with JQL, create or update Jira issues, analyze workflow states, batch-create tickets from requirements, export data for analysis, or manage epics. Key terms include search, create, update, analyze, export, ticket, issue, epic, JQL, workflow, state analysis, sprint, labels. Example user request colon "Find all open tickets in my project assigned to me" → `/jira` → search for assigned-to-me tickets with current status and open state.
---

# Jira Ticket Management

Complete Jira operations platform for searching, creating, updating, analyzing, and exporting tickets and epics.

## Quick Navigation

**Core Operations:**
- **Search & Query** — Find tickets using JQL (project, status, assignee, date range, labels)
- **Create Tickets** — Add new issues (task, story, bug) with proper formatting and epic linking
- **Update & Comment** — Modify existing tickets, change status, add comments
- **Manage Epics** — Create epics, list issues, enrich with details and child ticket analysis
- **Export & Analyze** — Download ticket data (CSV, JSON) and perform state duration analysis

**Advanced Workflows:**
- **Batch Operations** — Create multiple tickets from requirements lists
- **State Analysis** — Analyze how long tickets spend in each workflow state
- **Start Ticket** — Comprehensive ticket intake (analyze, create implementation plan, set up workspace)
- **Ticket Details** — Get full issue information including transitions and fields

---

## Operation Categories

### Search & Retrieve

Use when you need to find specific tickets or analyze existing issues.

**Commands:**
- `/jira:search [jql-query]` — Search with JQL (supports complex queries, pagination, format options)
- `/jira:get TICKET-KEY` — Get full details for a specific ticket
- `/jira:my-tickets` — Show all tickets assigned to you (quick status view)
- `/jira:epics` — List all epics in your project
- `/jira:epic-details EPIC-KEY` — Get epic details with child ticket breakdown
- `/jira:transitions TICKET-KEY` — Show available workflow transitions for a ticket

**Common JQL Patterns:**
- By project: `project = PROJ`
- By status: `status IN ('To Do', 'In Progress')`
- By assignee: `assignee = currentUser()` or `assignee = 'user@example.com'`
- Date range: `created >= 2024-01-01 AND created <= 2024-12-31`
- By epic: `parent = PROJ-100`
- By label: `labels = authentication`
- Complex: `project = PROJ AND status = Open AND priority = High`

### Create & Update

Use when adding new tickets, modifying existing ones, or linking to epics.

**Commands:**
- `/jira:create-ticket [summary] [optional: epic-key]` — Create single ticket with auto-formatting
- `/jira:create` — Create basic issue (simpler than create-ticket)
- `/jira:batch-create` — Create multiple tickets from requirements list
- `/jira:create-epic [name]` — Create new epic with structure and breakdown
- `/jira:update TICKET-KEY` — Modify status, description, fields
- `/jira:comment TICKET-KEY` — Add comment to existing ticket
- `/jira:enrich-epic EPIC-KEY` — Enhance epic with ADF-formatted content and child analysis

**Document Formatting:**
When creating or updating tickets, use ADF (Atlassian Document Format) for rich formatting. See `references/jira-document-formatting.md` for patterns.

### Export & Analyze

Use when exporting ticket data for external tools or analyzing workflow performance.

**Commands:**
- `/jira:export [jql-query]` — Export tickets to CSV, JSON, or JSONL format
- `/jira:analyze-states [jql-query or ticket-key]` — Analyze time spent in each workflow state

**Analysis Features:**
- Calendar days and business hours (9 AM–5 PM, weekdays)
- State transition history
- Bottleneck identification (longest-running states)
- Cycle time metrics
- CSV export for spreadsheet analysis

See `references/jira-state-analysis.md` for advanced patterns.

---

## Common Workflows

### Workflow 1: Quick Search & Status Check
```
1. Use /jira:search with JQL: "assignee = currentUser() AND status IN ('To Do', 'In Progress')"
2. Review results in table format
3. Click ticket links to open in Jira
```

### Workflow 2: Create Single Ticket
```
1. Use /jira:create-ticket "Add user authentication feature"
2. Optionally link to epic: /jira:create-ticket "Auth feature" PROJ-100
3. System formats description, applies labels, and confirms creation
```

### Workflow 3: Batch Create from Requirements
```
1. Prepare requirements list (text or markdown)
2. Use /jira:batch-create with requirements
3. System parses, creates tickets, applies epic linking
4. Confirm creation and review generated tickets
```

### Workflow 4: Analyze Project Performance
```
1. Use /jira:export "project = PROJ AND created >= 2024-01-01" to export data
2. Use /jira:analyze-states "project = PROJ" to calculate state durations
3. Review bottlenecks and cycle time metrics
4. Identify workflow improvements
```

### Workflow 5: Epic Management
```
1. Create epic: /jira:create-epic "Q1 Authentication System"
2. Add tickets to epic: /jira:create-ticket "OAuth2 flow" PROJ-100
3. Review epic structure: /jira:epic-details PROJ-100
4. Enrich with details: /jira:enrich-epic PROJ-100
```

---

## API Integration Patterns

For advanced operations, the Jira API supports:

- **JQL Queries** — Complex filtering with AND/OR/NOT logic
- **Expanded Fields** — Include changelog, history, worklogs
- **Pagination** — Handle large result sets (max 50 results per page)
- **Field Customization** — Select specific fields to minimize payload
- **Bulk Operations** — Create/update multiple tickets in single workflow

See `references/jira-api-patterns.md` for API-level details.

---

## When to Use This Skill

**Use `/jira` when:**
- Searching for tickets (JQL queries, quick views, detailed analysis)
- Creating or updating tickets (single, batch, with epic linking)
- Analyzing workflow metrics (state durations, bottlenecks, cycle time)
- Exporting data (CSV, JSON for external tools, reporting)
- Managing epics (create, list, enrich, analyze child tickets)
- Starting ticket implementation (intake, analysis, planning)

**Before Using:**
- Have your Jira project key (e.g., `PROJ`, `PROJ`)
- Know your search criteria (status, assignee, date range, epic)
- For batch operations, prepare requirements in text or markdown format

**Output Formats:**
- **Table** — Quick scanning, terminal display
- **JSON** — For further processing or APIs
- **CSV** — For spreadsheet analysis and reporting
- **Direct links** — Clickable Jira ticket URLs

---

## Reference Materials

For specialized operations, see:
- `references/jira-document-formatting.md` — ADF patterns for rich text in descriptions
- `references/jira-api-patterns.md` — API queries, pagination, field selection
- `references/jira-state-analysis.md` — Workflow bottleneck analysis and cycle time metrics
- `references/jira-batch-operations.md` — Bulk ticket creation from requirements

---

## Tips & Best Practices

**Searching:**
- Use project key prefix for specificity: `project = PROJ`
- Combine multiple criteria with AND: `status = Open AND priority = High`
- Date ranges: `created >= 2024-01-01 AND created <= 2024-12-31`
- Use `assignee = currentUser()` for quick personal views

**Creating:**
- Provide clear, actionable summaries (not vague titles)
- Link to epic when creating related tickets
- Use labels for categorization (authentication, infrastructure, ui)
- Include acceptance criteria in description

**Analyzing:**
- Always export with changelog for state analysis: `--expand changelog`
- Business hours mode (9-5, weekdays) reveals scheduling patterns
- Look for states with >50% of cycle time (workflow bottlenecks)
- Compare average times to identify outliers

**Exporting:**
- Use CSV for spreadsheet pivot tables
- Use JSON for programmatic analysis
- Include pagination info for large datasets
- Filter by date range to focus analysis
