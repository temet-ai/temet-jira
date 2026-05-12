Export Jira issues with advanced filtering.

Usage: /export PROJ --format csv -o tickets.csv

Execute: `jira-tool export $ARGUMENTS`

Common options:
- `--project PROJ` - Filter by project
- `--status "In Progress"` - Filter by status
- `--assignee "me"` - Filter by assignee
- `--format csv|json|jsonl|table` - Output format
- `-o filename` - Output to file
- `--all` - Export all results (no limit)
- `--expand changelog` - Include state history
