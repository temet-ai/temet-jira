# temet-jira

A comprehensive Jira API client and CLI tool for interacting with Jira Cloud instances.
Built for AI agents and automation workflows — retrieve tickets, create rich ADF content, and analyze workflow state durations.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [First Commands](#first-commands)
- [CLI Commands](#cli-commands)
- [MCP Server](#mcp-server)
- [Claude Code Integration](#claude-code-integration)
- [Python API](#python-api)
- [Development](#development)
- [Requirements](#requirements)

## Features

- **Agent-First Design** — Enable AI agents to retrieve tickets, parse requirements, and create implementation plans
- **Jira API Client** — Python and CLI interface to Jira Cloud REST API v3
- **Structured Data Export** — Export issues in JSON, JSONL, CSV formats optimized for agent processing
- **Document Builder** — Programmatically create ADF-formatted issues and epics with proper structure
- **Workflow Analysis** — Analyze state durations and bottlenecks for retrospectives
- **Epic Management** — Retrieve epics with children, filter by sprint, group by assignee/status
- **JQL Support** — Advanced filtering for complex queries and batch operations
- **Claude Code Integration** — Skills, slash commands, and an MCP server for AI-assisted workflows

## Quick Start

### Installation

**Recommended: install as a global tool with uv**

```bash
uv tool install temet-jira
```

**Alternative: pipx**

```bash
pipx install temet-jira
```

Verify:

```bash
temet-jira --help
```

### Configuration

Run the interactive setup wizard:

```bash
temet-jira setup
```

This guides you through:
1. Your Jira URL (e.g. `https://your-company.atlassian.net`)
2. Your email address
3. API token — generate one at https://id.atlassian.com/manage-profile/security/api-tokens
4. Optional default project key

Configuration is saved to `~/.config/temet-jira/config.yaml`.

**Alternative: environment variables**

```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_DEFAULT_PROJECT="PROJ"   # optional
```

Check your current configuration at any time:

```bash
temet-jira config show
```

### First Commands

```bash
# Get issue details
temet-jira get PROJ-123

# Search for issues using JQL
temet-jira search "project = PROJ AND status = 'In Progress'"

# List available issue types for a project
temet-jira types --project PROJ

# Create a task
temet-jira create --project PROJ --type Task --summary "Fix login bug"

# Export to CSV
temet-jira export --project PROJ --format csv -o tickets.csv
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `setup` | Interactive setup wizard |
| `config` | View and manage configuration (`show`, `get`, `set`, `unset`, `path`, `edit`) |
| `get` | Get details of a Jira issue |
| `search` | Search for issues using JQL |
| `types` | List available issue types for a project |
| `create` | Create a new issue with ADF formatting |
| `update` | Update issue fields or transition status |
| `comment` | Add a comment to an issue |
| `transitions` | Show available status transitions for an issue |
| `epics` | List all epics in a project |
| `epic-details` | Get epic details with child issues |
| `export` | Export issues with filtering (JSON, JSONL, CSV, table) |
| `analyze` | Analyze workflow state durations |

**Examples:**

```bash
temet-jira get PROJ-123                                  # Issue details
temet-jira search "assignee = currentUser()"            # JQL search
temet-jira types --project PROJ                         # Available issue types
temet-jira create --project PROJ --type Story \
    --summary "New feature" --priority High             # Create issue
temet-jira update PROJ-123 --status "Done"              # Transition status
temet-jira comment PROJ-123 "Deployed to staging"       # Add comment
temet-jira export --project PROJ --format jsonl \
    -o issues.jsonl                                     # Export (streaming)
temet-jira analyze state-durations issues.json          # Workflow analysis
```

**Output formats:** `table` (console default), `json`, `jsonl` (streaming, best for large datasets), `csv`

## MCP Server

`temet-jira` ships with a built-in MCP server for Claude Code and other MCP-compatible hosts:

```bash
temet-jira-mcp
```

Add it to your `~/.claude.json` MCP configuration to expose Jira tools directly to Claude.

## Claude Code Integration

Slash commands are available in `.claude/commands/` when working inside this repository:

| Command | Description |
|---------|-------------|
| `/get PROJ-123` | Get ticket details |
| `/search "JQL query"` | Search with JQL |
| `/create` | Create an issue |
| `/update PROJ-123` | Update an issue |
| `/comment PROJ-123 "message"` | Add a comment |
| `/export` | Export issues |
| `/epics` | List epics |
| `/epic-details PROJ-123` | Epic with children |
| `/transitions PROJ-123` | Show transitions |

Skills in `.claude/skills/` provide reference documentation for Claude:

| Skill | Description |
|-------|-------------|
| `jira-api` | Jira REST API v3 documentation, endpoints, JQL patterns |
| `jira-builders` | CLI usage guide and best practices |
| `build-jira-document-format` | ADF builder patterns |
| `work-with-adf` | Atlassian Document Format creation |

## Python API

```python
from temet_jira import JiraClient, IssueBuilder, EpicBuilder

# Fetch an issue
client = JiraClient()
issue = client.get_issue("PROJ-123")

# Create a structured issue with ADF content
builder = IssueBuilder(title="New feature", story_points=8)
builder.add_description("Feature description")
builder.add_acceptance_criteria(["Criteria 1", "Criteria 2"])

client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "New feature",
    "issuetype": {"name": "Story"},
    "description": builder.build(),
})
```

Also available: `JiraDocumentBuilder` (raw ADF builder), `SubtaskBuilder`, `StateDurationAnalyzer`.

## Development

```bash
# Clone and install dev dependencies
git clone https://github.com/temet-ai/temet-jira.git
cd temet-jira
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=temet_jira

# Lint and type check
uv run ruff check src/ tests/
uv run mypy src/

# After code changes, rebuild the installed binary
uv build && uv tool install . --force --refresh-package temet-jira
```

### Project Structure

```
temet-jira/
├── src/temet_jira/          # Main package
│   ├── client.py            # JiraClient API
│   ├── formatter.py         # Document builders (legacy entry point)
│   ├── cli.py               # CLI commands
│   ├── mcp_server.py        # MCP server
│   ├── document/            # ADF document builder
│   └── analysis/            # State duration analysis
├── .claude/
│   ├── commands/            # Slash commands for Claude Code
│   └── skills/              # Reference skills
├── tests/                   # Test suite
└── pyproject.toml
```

## Requirements

- **Python 3.11+**
- **uv** or **pipx** for installation
- **Jira Cloud** (REST API v3)
- **Valid Jira API token**

## License

MIT

## Support

- Open an issue at https://github.com/temet-ai/temet-jira/issues
