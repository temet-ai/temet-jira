# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A comprehensive Jira API client and CLI tool for interacting with Jira Cloud instances. The tool provides both programmatic Python access and a rich command-line interface with state analysis capabilities.

**Key Features:**
- Full Jira REST API v3 client
- Rich CLI with multiple output formats (table, JSON, CSV)
- Atlassian Document Format (ADF) document builder for rich content
- State duration analysis for workflow tracking
- Epic and issue management utilities

## Coding Principles

This project follows **Single Responsibility Principle** and **DRY (Don't Repeat Yourself)** practices:

### CRITICAL: Avoid Multiple Scripts for Same Purpose

**Anti-Pattern to AVOID:**
- Creating multiple separate scripts that do the same thing with slight variations
- Example: `pull_tickets_basic.py`, `pull_tickets_filtered.py`, `pull_tickets_csv.py`, `pull_tickets_advanced.py`
- This violates single responsibility and creates maintenance burden

**Correct Pattern:**
- Create ONE script/CLI command with configurable options via command-line arguments
- Use argparse/click to handle different modes, output formats, and filtering
- Example: `pull_tickets.py --format csv --filter status=Open --output file.csv`

**When Creating New Functionality:**
1. Check if existing CLI commands can be extended with new flags/options
2. If creating a script, make it configurable rather than creating variants
3. Prefer enhancing `src/jira_tool/cli.py` over creating standalone scripts
4. Use the existing CLI architecture (Click-based) for consistency

**Script Guidelines:**
- Scripts in `src/jira_tool/scripts/` should be for specific, one-off use cases only
- For reusable functionality, add commands to the main CLI (`cli.py`)
- Each script should have a single, well-defined purpose
- Use command-line arguments for variations, not separate scripts

## Development Commands

### Package Management
This project uses `uv` for dependency management:
```bash
# Install dependencies
uv sync

# Run CLI commands
uv run jira-tool [command]

# Run Python scripts
uv run python -m jira_tool.[module]
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=jira_tool

# Run specific test file
uv run pytest tests/test_client.py

# Run specific test function
uv run pytest tests/test_client.py::test_function_name

# Run tests matching pattern
uv run pytest -k "test_state"
```

### Code Quality
```bash
# Format code (auto-fix)
uv run black src/ tests/

# Lint code
uv run ruff src/ tests/

# Type check
uv run mypy src/
```

**Important:** Always run linting and tests after making code changes. The project enforces strict type checking with `disallow_untyped_defs = true`.

### Install vs Development

This tool is installed as a **uv global tool**. There are two execution modes:

| Mode | Command | When to use |
|------|---------|-------------|
| Development | `uv run jira-tool [command]` | During coding — picks up edits instantly |
| Installed binary | `jira-tool [command]` | What users actually run — requires rebuild |

**After any code change that needs to be in the installed binary:**
```bash
uv build && uv tool install . --force --refresh-package jira-tool
```

**DO NOT** use `uv pip install -e .` — this is WRONG for this project. Changes will NOT affect the `jira-tool` binary.

**Critical:** Never declare a CLI change "done" without rebuilding. Tests pass against development code; users run the installed binary.

### Done Checklist

Before declaring ANY CLI work complete, follow this sequence:

1. Tests pass: `uv run python -m pytest tests/ -x -q`
2. Rebuild tool: `uv build && uv tool install . --force --refresh-package jira-tool`
3. Run real command: `jira-tool <command> <real-args>` and inspect output
4. For format changes: compare output against Jira web UI to confirm nothing is missing

## Architecture

### Core Components

**JiraClient** (`src/jira_tool/client.py`)
- Main API client with session management and retry logic
- Handles authentication via Basic Auth with API tokens
- Provides methods for all Jira operations (issues, search, projects, etc.)
- Auto-discovers custom fields (e.g., Epic Link field)

**JiraDocumentBuilder** (`src/jira_tool/formatter.py`)
- Fluent builder for creating Atlassian Document Format (ADF) content
- Specialized builders: `EpicBuilder` and `IssueBuilder` for standardized layouts
- Methods for headings, paragraphs, lists, panels, code blocks, and text formatting
- Call `.build()` to get final ADF dictionary for Jira API

**StateDurationAnalyzer** (`src/jira_tool/analysis/state_analyzer.py`)
- Analyzes issue changelog to track time spent in each state
- Calculates both calendar days and business hours (9 AM - 5 PM, weekdays only)
- Extracts state transitions from changelog history
- Exports results to CSV format

**CLI** (`src/jira_tool/cli.py`)
- Click-based command-line interface with Rich formatting
- Commands: `get`, `search`, `create`, `update`, `comment`, `transitions`, `epics`, `epic-details`, `export`
- Subgroup: `analyze state-durations` for workflow analysis
- Supports `--format` (table/json/csv/jsonl) and `--output` for file export

### ADF Extractor (`src/jira_tool/document/adf/extractor.py`)

When modifying the ADF extractor:

1. Reference the [Atlassian ADF spec](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/) before declaring complete
2. Compare implemented handlers against all node types in the spec
3. Unknown nodes must never silently drop content — use the fallback chain: `node.text` → `attrs.text` → `attrs.url` → log debug
4. After rebuild, run `jira-tool get <real-issue-key>` against a real Jira issue with rich content and inspect the description output
5. "Tests pass" is not sufficient — ADF content from real Jira issues is more varied than test fixtures

## Available Slash Commands

**Location:** All slash commands are in `.claude/commands/jira/` - type `/jira:` and tab to see all options.

**Full Reference:** See `.claude/commands/jira/README.md` for complete documentation.

### Quick Reference - What to Use When

**Viewing Issues:**
- `/jira:get PROJ-123` - View single issue details
- `/jira:my-tickets` - Your active tickets
- `/jira:search "project = PROJ"` - Search with JQL

**Creating Issues:**
- `/jira:create` - Simple issues (uses CLI directly)
- `/jira:create-ticket` - Complex issues (uses agent for formatting)
- `/jira:create-epic` - New epics with structure

**Modifying Issues:**
- `/jira:update PROJ-123 --status "Done"` - Update fields/status
- `/jira:comment PROJ-123 "message"` - Add comment

**Data Export:**
- `/jira:export PROJ --format csv -o file.csv` - Export to CSV
- `/jira:export PROJ --all --format jsonl -o file.jsonl` - Export all (JSONL recommended for large datasets)
- **Formats:** table (console), json, jsonl (streaming), csv (spreadsheet)

**Workflow Analysis:**
```bash
# 1. Export with changelog
uv run jira-tool export PROJ --expand changelog --format json -o issues.json
# 2. Analyze durations
uv run jira-tool analyze state-durations issues.json -o durations.csv
```

### Data Flow for State Analysis

1. Fetch issues with `expand=changelog` via `JiraClient.search_issues()`
2. Parse changelog to extract `StateTransition` objects via `StateDurationAnalyzer.extract_state_transitions()`
3. Calculate durations between transitions via `calculate_durations()`
4. Format results via `format_as_csv()` or analysis formatters

### Configuration

Environment variables (required):
- `JIRA_BASE_URL`: Your Jira instance URL (e.g., `https://company.atlassian.net`)
- `JIRA_USERNAME`: Email address for authentication
- `JIRA_API_TOKEN`: API token from Jira user settings

Optional environment variables:
- `JIRA_DEFAULT_PROJECT`: Default project key for commands (e.g., `PROJ`)
- `JIRA_DEFAULT_COMPONENT`: Default component filter for export/search commands (e.g., `"Backend"`)
- `JIRA_DEFAULT_FORMAT`: Default output format for get/search/export (`table`, `json`, `jsonl`, `csv`)
- `JIRA_DEFAULT_MAX_RESULTS`: Default max results per query (default: 300)

All optional settings can also be set via `temet-jira config set <key> <value>`.

## Common Patterns

### Working with ADF (Atlassian Document Format)

When creating or updating issues with rich content:
```python
from jira_tool.formatter import JiraDocumentBuilder

doc = JiraDocumentBuilder()
doc.add_heading("Title", 1)
doc.add_paragraph(doc.bold("Key: "), doc.add_text("Value"))
doc.add_bullet_list(["Item 1", "Item 2"])
adf_content = doc.build()  # Returns ADF dict for API
```

### Custom Field Discovery

Epic Link and other custom fields vary by Jira instance. The client auto-discovers them:
- `get_custom_field_id(field_name)`: Get field ID by name
- `get_epic_link_field()`: Tries common field IDs (customfield_11923, customfield_10014, etc.)
- Check `client.py:295-308` for Epic Link logic

### Expanding Fields

To get changelog or other expanded data:
```python
# Single issue
issue = client.get_issue("PROJ-123", expand=["changelog", "transitions"])

# Search
issues = client.search_issues(jql, expand=["changelog"])
```

**Critical:** State duration analysis requires `expand=["changelog"]` to function.

### Output Formatters

The analysis module has separate formatters:
- `format_as_json()` in `analysis/formatters.py` - for issue data (pretty-printed)
- `format_as_jsonl()` in `analysis/formatters.py` - for issue data (streaming, one per line)
- `format_as_csv()` in `analysis/formatters.py` - for issue data (spreadsheet-compatible)
- `StateDurationAnalyzer.format_as_csv()` in `state_analyzer.py` - for duration analysis

Don't confuse these - use the appropriate formatter for your data type.

**Format Selection Guidelines:**
- **JSONL**: Best for large datasets, streaming, line-by-line processing
- **JSON**: Best for readability and small-to-medium datasets
- **CSV**: Best for spreadsheet analysis and non-technical users
- **Table**: Best for console viewing (not saveable to file)

## Testing Strategy

### Test Organization
- `tests/` - CLI integration tests
- `tests/cli/` - CLI command tests
- `tests/analysis/` - State analyzer tests with fixtures
- `tests/fixtures/` - Shared test data

### Key Fixtures
- `jira_client` (conftest.py): Mocked JiraClient with test credentials
- `mock_response`: Pre-configured mock response for API calls
- Test data in `tests/fixtures/jira_data.py` for state analysis

### Mocking Guidelines
Always mock API calls using `patch` on the session or `_request` method:
```python
with patch.object(client.session, 'request') as mock_request:
    mock_request.return_value.json.return_value = {...}
    result = client.get_issue("TEST-1")
```

## Project-Specific Notes

- The tool assumes Jira Cloud (REST API v3), not Jira Server/Data Center
- Custom field IDs in hardcoded commands (cli.py:354) may need adjustment for your instance
- Business hours calculation assumes UTC timezone unless specified
