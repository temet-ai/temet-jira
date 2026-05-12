Create a new Jira issue.

Usage: /create --project PROJ --type Task --summary "Title"

Execute: `jira-tool create $ARGUMENTS`

Common options:
- `--project PROJ` - Project key (required)
- `--type Task|Story|Bug|Epic` - Issue type (required)
- `--summary "Title"` - Issue summary (required)
- `--description "Text"` - Issue description
- `--parent PROJ-123` - Parent issue (for subtasks/stories under epics)
- `--priority High|Medium|Low` - Priority level
