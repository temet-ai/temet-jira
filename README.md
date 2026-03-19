# Jira Tool

A comprehensive Jira API client and CLI tool for interacting with Jira Cloud instances.
Useful to automate workflows, create rich ADF content, and analyze workflow state durations.
Use it in your agents / prompts / instructions for AI agents, or build automation scripts.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [First Commands](#first-commands)
- [CLI Commands](#cli-commands)
- [Claude Code Integration](#claude-code-integration)
  - [Slash Commands](#slash-commands)
  - [Skills](#skills)
  - [Prompts](#prompts)
- [Python API](#python-api)
- [Documentation](#documentation)
- [Development](#development)
- [Requirements](#requirements)

## Features

**Built for AI agents and automation workflows:**

- **Agent-First Design** - Enable AI agents to retrieve tickets, parse requirements, and create implementation plans
- **Jira API Client** - Python and CLI interface to Jira Cloud REST API v3
- **Structured Data Export** - Export issues in JSON, JSONL, CSV formats optimized for agent processing
- **Document Builder** - Programmatically create ADF-formatted issues and epics with proper structure
- **Workflow Analysis** - Analyze state durations and bottlenecks for retrospectives
- **Epic & Sprint Management** - Retrieve epics with children, filter by sprint, group by assignee/status
- **JQL Support** - Advanced filtering for complex queries and batch operations
- **Claude Code Integration** - Skills, slash commands, and prompts for AI-assisted workflows

## Quick Start

### Installation

**Option 1: System-wide installation (recommended)**

Install globally so `jira-tool` is available anywhere:

```bash
# Clone the repository
git clone <repository-url>
cd jira-tool

# Build and install
./scripts/build_and_install.sh

# Verify installation
jira-tool --help
```

**Option 2: Development installation**

For development or testing:

```bash
# Install with uv (recommended)
uv sync

# Run commands
uv run jira-tool --help
```

See [scripts/README.md](scripts/README.md) for more installation options.

### Configuration

Run the interactive setup wizard:

```bash
jira-tool setup
```

This will guide you through:
1. Entering your Jira URL
2. Your email address
3. API token (get one at https://id.atlassian.com/manage-profile/security/api-tokens)
4. Optional default project

Configuration is saved to `~/.config/jira-tool/config.yaml`.

**Alternative:** Set environment variables in your shell profile:
```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

See **[Getting Started](docs/guides/getting_started.md)** for detailed setup instructions.

### First Commands

```bash
# Get issue details
jira-tool get PROJ-123

# Search for issues
jira-tool search "project = PROJ AND status = Open"

# Create a task
jira-tool create --project PROJ --type Task --summary "Fix login bug"

# Export to CSV
jira-tool export --project PROJ --format csv -o tickets.csv

# View your active work
jira-tool export --assignee "me" --status "In Progress"
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `setup` | Interactive setup wizard |
| `config` | View and manage configuration |
| `get` | Get details of a Jira issue |
| `search` | Search for issues using JQL |
| `create` | Create a new issue with ADF formatting |
| `update` | Update issue fields or transition status |
| `comment` | Add a comment to an issue |
| `transitions` | Show available status transitions |
| `epics` | List all epics in a project |
| `epic-details` | Get epic details with child issues |
| `export` | Export issues with filtering (JSON, CSV, JSONL) |
| `analyze` | Analyze workflow state durations |

**Examples:**
```bash
jira-tool get PROJ-123                          # Get issue details
jira-tool search "status = 'In Progress'"       # Search with JQL
jira-tool create --project PROJ --type Epic --summary "New feature"
jira-tool update PROJ-123 --status "Done"       # Transition status
jira-tool export --assignee "me" --format csv   # Export your tickets
jira-tool analyze state-durations issues.json   # Workflow analysis
```

**See:** [CLI Reference](docs/reference/cli_reference.md) for all commands and [Usage Guide](docs/guides/usage_guide.md) for workflows.

## Claude Code Integration

This project includes full Claude Code support with slash commands, skills, and prompts for AI-assisted Jira workflows.

### Slash Commands

Available in `.claude/commands/` - use with `/command-name` in Claude Code:

| Command | Description |
|---------|-------------|
| `/get PROJ-123` | Get ticket details |
| `/search "JQL query"` | Search with JQL |
| `/create --project PROJ ...` | Create an issue |
| `/update PROJ-123 --status "Done"` | Update an issue |
| `/comment PROJ-123 "message"` | Add a comment |
| `/export --project PROJ ...` | Export issues |
| `/epics --project PROJ` | List epics |
| `/epic-details PROJ-123` | Epic with children |
| `/transitions PROJ-123` | Show transitions |

### Skills

Available in `.claude/skills/` - reference guides for Claude:

| Skill | Description |
|-------|-------------|
| `jira-api` | Jira REST API v3 documentation, endpoints, JQL patterns |
| `jira-builders` | CLI usage guide and best practices |
| `build-jira-document-format` | ADF builder patterns with EpicBuilder/IssueBuilder |
| `work-with-adf` | Atlassian Document Format creation and validation |

### Prompts

GitHub Copilot-style prompts in `.github/prompts/` for complex workflows:

| Prompt | Description |
|--------|-------------|
| `jira-ticket-retriever` | Fetch and archive tickets to artifact directories |
| `jira-task-parser` | Transform tickets into implementation plans |
| `jira-orchestration-lead` | Coordinate retrieval, parsing, and planning |

**Workflow Guide:** See `.github/instructions/jira-workflow-guide.instructions.md` for when to use each prompt.

## Python API

The Python API provides `JiraClient` for all Jira operations, document builders (`IssueBuilder`, `EpicBuilder`, `JiraDocumentBuilder`) for creating ADF-formatted content, and `StateDurationAnalyzer` for workflow analysis.

**Quick example:**
```python
from jira_tool import JiraClient, IssueBuilder

# Get issues and create structured content
client = JiraClient()
issue = client.get_issue("PROJ-123")

builder = IssueBuilder(title="New feature", story_points=8)
builder.add_description("Feature description")
builder.add_acceptance_criteria(["Criteria 1", "Criteria 2"])

client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "New feature",
    "issuetype": {"name": "Task"},
    "description": builder.build()
})
```

**See:** [Python API Guide](docs/guides/python_api_guide.md) for complete API documentation.

## Documentation

### Guides

- **[Getting Started](docs/guides/getting_started.md)** - Quick 5-minute setup and first commands
- **[Setup Guide](docs/guides/jira_setup.md)** - Detailed configuration, API tokens, troubleshooting
- **[Usage Guide](docs/guides/usage_guide.md)** - Common workflows, sprint planning, data export
- **[Python API Guide](docs/guides/python_api_guide.md)** - Complete API reference with examples
- **[Formatting Guide](docs/guides/jira_formatting_guide.md)** - Create rich ADF content

### Reference

- **[CLI Reference](docs/reference/cli_reference.md)** - Complete command documentation
- **[ADF Reference](docs/reference/adf_reference_guide.md)** - Atlassian Document Format structure

### Examples

- **[examples/create_issue_with_proper_formatting.py](examples/create_issue_with_proper_formatting.py)** - IssueBuilder and EpicBuilder examples

## Development

### Setup Development Environment

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=jira_tool

# Format code
uv run black src/ tests/

# Lint code
uv run ruff src/ tests/

# Type check
uv run mypy src/
```

### Project Structure

```
jira-tool/
├── src/jira_tool/           # Main package
│   ├── client.py            # JiraClient API
│   ├── formatter.py         # Document builders
│   ├── cli.py               # CLI commands
│   └── analysis/            # State analysis
├── .claude/                 # Claude Code integration
│   ├── commands/            # Slash commands (/get, /search, etc.)
│   └── skills/              # Reference skills (jira-api, etc.)
├── .github/                 # GitHub integration
│   ├── prompts/             # AI prompts for workflows
│   └── instructions/        # Workflow guides
├── docs/                    # Documentation
│   ├── guides/              # User guides
│   └── reference/           # API reference
├── examples/                # Example scripts
├── tests/                   # Test suite
└── scripts/                 # Build and install scripts
```

### Code Quality

The project enforces:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking (strict mode)
- **Pytest** for testing

```bash
# Format, lint, and test
uv run black src/ tests/
uv run ruff src/ tests/
uv run pytest
```

## Requirements

- **Python 3.11+**
- **Jira Cloud** (REST API v3)
- **Valid Jira API token**

## License

This project is distributed as-is without a specific license.

## Support

For issues and questions:
- Check the [documentation](docs/)
- Review the [examples](examples/)
- Create an issue in the repository

---

**Quick Links:**
- [Getting Started](docs/guides/getting_started.md)
- [Command Reference](docs/reference/cli_reference.md)
- [Python API](docs/guides/python_api_guide.md)
- [Examples](examples/)
