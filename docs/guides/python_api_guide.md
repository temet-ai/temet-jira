# Python API Guide

Complete guide to using the `temet-jira` Python API programmatically.

## Table of Contents

- [Getting Started](#getting-started)
- [JiraClient](#jiraclient)
- [Document Builders](#document-builders)
  - [JiraDocumentBuilder](#jiradocumentbuilder)
  - [IssueBuilder](#issuebuilder)
  - [EpicBuilder](#epicbuilder)
- [State Analysis](#state-analysis)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)

## Getting Started

### Installation

```bash
pip install temet-jira
# or
uv add temet-jira
```

### Basic Usage

```python
from temet_jira import JiraClient

# Initialize client (uses environment variables)
client = JiraClient()

# Get an issue
issue = client.get_issue("PROJ-123")
print(f"Issue: {issue['key']} - {issue['fields']['summary']}")

# Search for issues
issues = client.search_issues("project = PROJ AND status = Open")
for issue in issues:
    print(f"{issue['key']}: {issue['fields']['summary']}")
```

### Configuration

The client reads configuration from environment variables:

```python
import os

# Set before initializing client
os.environ["JIRA_BASE_URL"] = "https://your-company.atlassian.net"
os.environ["JIRA_USERNAME"] = "your-email@example.com"
os.environ["JIRA_API_TOKEN"] = "your-api-token"

# Or pass directly to constructor
from temet_jira import JiraClient

client = JiraClient(
    base_url="https://your-company.atlassian.net",
    username="your-email@example.com",
    api_token="your-api-token"
)
```

## JiraClient

### Initialization

```python
from temet_jira import JiraClient

# Use environment variables (recommended)
client = JiraClient()

# Or explicit configuration
client = JiraClient(
    base_url="https://company.atlassian.net",
    username="user@example.com",
    api_token="token",
    timeout=30,  # Request timeout in seconds
    max_retries=3  # Retry attempts for failed requests
)
```

### Getting Issues

```python
# Get a single issue
issue = client.get_issue("PROJ-123")

# Get with expanded fields
issue = client.get_issue("PROJ-123", expand=["changelog", "transitions"])

# Access issue fields
print(f"Summary: {issue['fields']['summary']}")
print(f"Status: {issue['fields']['status']['name']}")
print(f"Assignee: {issue['fields']['assignee']['displayName']}")
```

### Searching Issues

```python
# Basic search
issues = client.search_issues("project = PROJ")

# With JQL
issues = client.search_issues(
    "project = PROJ AND status = 'In Progress'",
    max_results=50
)

# Get all results (handles pagination)
issues = client.search_issues(
    "project = PROJ",
    max_results=None  # Retrieve all
)

# With specific fields
issues = client.search_issues(
    "project = PROJ",
    fields=["summary", "status", "assignee"]
)

# With expanded fields
issues = client.search_issues(
    "project = PROJ",
    expand=["changelog"]
)

# Process results
for issue in issues:
    key = issue['key']
    summary = issue['fields']['summary']
    status = issue['fields']['status']['name']
    print(f"{key}: {summary} [{status}]")
```

### Creating Issues

```python
# Simple issue
new_issue = client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "Bug fix needed",
    "issuetype": {"name": "Bug"}
})

print(f"Created: {new_issue['key']}")

# Issue with full details
issue_data = {
    "project": {"key": "PROJ"},
    "summary": "Implement OAuth2 authentication",
    "issuetype": {"name": "Story"},
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Implement OAuth2-based authentication"}
                ]
            }
        ]
    },
    "priority": {"name": "High"},
    "labels": ["backend", "security"],
    "assignee": {"emailAddress": "dev@example.com"}
}

new_issue = client.create_issue(issue_data)
```

### Updating Issues

```python
# Update fields
client.update_issue("PROJ-123", {
    "summary": "Updated summary",
    "priority": {"name": "High"}
})

# Update description (ADF format)
client.update_issue("PROJ-123", {
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "New description"}
                ]
            }
        ]
    }
})

# Update labels
client.update_issue("PROJ-123", {
    "labels": ["urgent", "backend"]
})
```

### Transitions

```python
# Get available transitions
transitions = client.get_transitions("PROJ-123")
for transition in transitions:
    print(f"{transition['id']}: {transition['name']}")

# Transition issue
client.transition_issue("PROJ-123", "31")  # Transition ID

# Or find and transition by name
transitions = client.get_transitions("PROJ-123")
done_transition = next(t for t in transitions if t['name'] == 'Done')
client.transition_issue("PROJ-123", done_transition['id'])
```

### Comments

```python
# Add simple comment
client.add_comment("PROJ-123", "This looks good!")

# Add comment with ADF formatting
comment_body = {
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Review complete. "},
                {"type": "text", "text": "Approved", "marks": [{"type": "strong"}]}
            ]
        }
    ]
}
client.add_comment("PROJ-123", comment_body)
```

### Projects

```python
# Get all projects
projects = client.get_projects()
for project in projects:
    print(f"{project['key']}: {project['name']}")

# Get specific project
project = client.get_project("PROJ")
print(f"Project: {project['name']}")
print(f"Lead: {project['lead']['displayName']}")
```

## Document Builders

### JiraDocumentBuilder

Build Atlassian Document Format (ADF) content with a fluent API:

```python
from temet_jira.formatter import JiraDocumentBuilder

# Create builder
doc = JiraDocumentBuilder()

# Add content
doc.add_heading("My Document", level=1)
doc.add_paragraph("This is a paragraph with ", doc.bold("bold"), " text.")
doc.add_bullet_list(["Item 1", "Item 2", "Item 3"])
doc.add_code_block("print('Hello')", language="python")

# Build ADF structure
adf = doc.build()

# Use in issue creation
client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "Issue title",
    "issuetype": {"name": "Task"},
    "description": adf
})
```

#### Available Methods

**Headings:**
```python
doc.add_heading("Heading Text", level=1)  # level: 1-6
```

**Paragraphs:**
```python
doc.add_paragraph("Simple text")
doc.add_paragraph(doc.bold("Bold"), " and ", doc.italic("italic"))
doc.add_paragraph(doc.code("inline code"))
```

**Lists:**
```python
# Bullet list
doc.add_bullet_list(["Item 1", "Item 2", "Item 3"])

# Numbered list
doc.add_numbered_list(["Step 1", "Step 2", "Step 3"])
```

**Code Blocks:**
```python
doc.add_code_block("print('Hello')", language="python")
doc.add_code_block("SELECT * FROM users", language="sql")
```

**Panels:**
```python
doc.add_panel("Important note", panel_type="info")    # info, note, warning, error, success
doc.add_panel("Warning!", panel_type="warning")
```

**Text Formatting:**
```python
doc.bold("Bold text")
doc.italic("Italic text")
doc.code("Inline code")
doc.underline("Underlined text")
doc.strikethrough("Strikethrough text")
```

**Links:**
```python
doc.add_paragraph(
    "Visit ",
    doc.add_link("https://example.com", "our website")
)
```

### IssueBuilder

Specialized builder for creating well-structured issues and tasks:

```python
from temet_jira import JiraClient, IssueBuilder

client = JiraClient()

# Create builder
builder = IssueBuilder(
    title="Implement user authentication",
    component="Backend Services",
    story_points=8,
    epic_key="PROJ-100"
)

# Add structured sections
builder.add_description(
    "Implement OAuth2-based authentication for API endpoints"
)

builder.add_implementation_details([
    "Set up OAuth2 provider configuration",
    "Create authentication middleware",
    "Implement token refresh mechanism",
    "Add rate limiting for login attempts"
])

builder.add_acceptance_criteria([
    "Users can authenticate with corporate credentials",
    "Access tokens are generated on successful login",
    "Refresh tokens work correctly",
    "Rate limiting prevents brute force attacks"
])

builder.add_technical_notes(
    requirements=[
        "Use OAuth2 library (authlib)",
        "Store tokens in Redis",
        "Implement PKCE for security"
    ],
    code_example="from authlib.integrations.flask_client import OAuth",
    code_language="python"
)

builder.add_edge_cases([
    "Handle expired tokens gracefully",
    "Support multiple identity providers",
    "Handle network timeouts during auth"
])

builder.add_testing_considerations([
    "Unit tests for authentication flow",
    "Integration tests with mock OAuth provider",
    "Security testing for token handling"
])

# Build ADF and create issue
adf = builder.build()
issue = client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "Implement user authentication",
    "issuetype": {"name": "Task"},
    "description": adf,
    "priority": {"name": "High"},
    "labels": ["backend", "security"]
})
```

### EpicBuilder

Specialized builder for creating comprehensive epics:

```python
from temet_jira import JiraClient, EpicBuilder

client = JiraClient()

# Create epic builder
builder = EpicBuilder(
    title="Redesign User Dashboard",
    priority="P1",
    dependencies="Design system completion",
    services="Frontend, Backend API"
)

# Add all sections
builder.add_problem_statement(
    "Current dashboard is slow (5s load time) and lacks actionable insights. "
    "Users can't quickly understand their status or take action."
)

builder.add_description(
    "Complete redesign with modern UX patterns, improved performance, "
    "and better data visualization."
)

builder.add_technical_details(
    requirements=[
        "Implement React 18+ with Suspense",
        "Add Redux Toolkit for state management",
        "Integrate Recharts for visualizations",
        "Use React Query for data fetching"
    ],
    code_example="""
import { Suspense } from 'react';
import { DashboardWidget } from './DashboardWidget';

function Dashboard() {
  return (
    <Suspense fallback={<Loading />}>
      <DashboardWidget />
    </Suspense>
  );
}
    """.strip(),
    code_language="javascript"
)

builder.add_acceptance_criteria([
    "Dashboard loads in under 2 seconds",
    "All widgets are interactive and update in real-time",
    "Full accessibility compliance (WCAG 2.1 AA)",
    "Works on mobile devices (responsive design)"
])

builder.add_edge_cases([
    "Handle missing or incomplete data gracefully",
    "Support users with limited bandwidth",
    "Handle API failures with retry logic",
    "Support offline mode with cached data"
])

builder.add_testing_considerations([
    "Unit tests for all components (>80% coverage)",
    "E2E tests for critical user workflows",
    "Performance testing under load",
    "Accessibility testing with screen readers"
])

# Build and create epic
adf = builder.build()
epic = client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "Redesign User Dashboard",
    "issuetype": {"name": "Epic"},
    "description": adf,
    "priority": {"name": "Highest"},
    "labels": ["frontend", "ux"]
})

print(f"Created epic: {epic['key']}")
```

## State Analysis

Analyze how long issues spent in each workflow state:

```python
from temet_jira import JiraClient
from temet_jira.analysis import StateDurationAnalyzer

client = JiraClient()

# Get issues with changelog
issues = client.search_issues(
    "project = PROJ AND created >= -30d",
    expand=["changelog"],
    max_results=None
)

# Analyze state durations
analyzer = StateDurationAnalyzer()
results = analyzer.analyze_issues(issues)

# Export to CSV
csv_output = analyzer.format_as_csv(
    results,
    include_business_hours=True
)

with open("state_durations.csv", "w") as f:
    f.write(csv_output)

# Or process programmatically
for issue_key, states in results.items():
    print(f"\n{issue_key}:")
    for state in states:
        print(f"  {state.state}: {state.duration_calendar_days:.1f} days")
```

### StateDurationAnalyzer Methods

```python
from temet_jira.analysis import StateDurationAnalyzer

analyzer = StateDurationAnalyzer()

# Analyze issues
results = analyzer.analyze_issues(issues)
# Returns: Dict[str, List[StateDuration]]

# Extract transitions from changelog
transitions = analyzer.extract_state_transitions(issue)
# Returns: List[StateTransition]

# Calculate durations from transitions
durations = analyzer.calculate_durations(transitions)
# Returns: List[StateDuration]

# Format as CSV
csv = analyzer.format_as_csv(results, include_business_hours=True)
# Returns: str
```

### StateDuration Data Class

```python
from temet_jira.analysis.state_analyzer import StateDuration

# StateDuration attributes:
duration.state                    # str: State name
duration.duration_calendar_days   # float: Days including weekends
duration.duration_business_hours  # float: Business hours (9 AM - 5 PM, weekdays)
```

## Error Handling

### Exception Types

```python
from requests.exceptions import HTTPError, ConnectionError, Timeout

try:
    issue = client.get_issue("PROJ-123")
except HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.response.status_code == 403:
        print("Permission denied - insufficient access")
    elif e.response.status_code == 404:
        print("Issue not found")
    else:
        print(f"HTTP error: {e}")
except ConnectionError:
    print("Network connection failed")
except Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

The client includes automatic retry logic:

```python
# Customize retry behavior
client = JiraClient(
    base_url="https://company.atlassian.net",
    username="user@example.com",
    api_token="token",
    max_retries=5,      # More retries
    timeout=60          # Longer timeout
)
```

### Validation

```python
# Validate before operations
try:
    # Check if issue exists
    issue = client.get_issue("PROJ-123")

    # Then update
    client.update_issue("PROJ-123", {"summary": "New summary"})
except HTTPError as e:
    if e.response.status_code == 404:
        print("Cannot update - issue doesn't exist")
```

## Advanced Usage

### Pagination

```python
# Manual pagination
start_at = 0
max_results = 50
all_issues = []

while True:
    response = client.search_issues(
        "project = PROJ",
        start_at=start_at,
        max_results=max_results
    )

    all_issues.extend(response['issues'])

    if len(response['issues']) < max_results:
        break

    start_at += max_results

# Or use max_results=None for automatic pagination
issues = client.search_issues("project = PROJ", max_results=None)
```

### Custom Fields

```python
# Discover custom fields
field_id = client.get_custom_field_id("Story Points")
print(f"Story Points field: {field_id}")

# Get epic link field
epic_field = client.get_epic_link_field()

# Use in search
issues = client.search_issues(
    f"project = PROJ AND '{epic_field}' = PROJ-100"
)

# Set custom fields
client.update_issue("PROJ-123", {
    field_id: 8  # Set story points to 8
})
```

### Bulk Operations

```python
# Bulk create
issues_to_create = [
    {
        "project": {"key": "PROJ"},
        "summary": f"Task {i}",
        "issuetype": {"name": "Task"}
    }
    for i in range(10)
]

created = []
for issue_data in issues_to_create:
    issue = client.create_issue(issue_data)
    created.append(issue['key'])
    print(f"Created: {issue['key']}")

# Bulk update
issues_to_update = client.search_issues("status = 'To Do' AND priority is EMPTY")
for issue in issues_to_update:
    client.update_issue(issue['key'], {"priority": {"name": "Medium"}})
    print(f"Updated: {issue['key']}")
```

### Working with Attachments

```python
# Get issue with attachments
issue = client.get_issue("PROJ-123")
attachments = issue['fields'].get('attachment', [])

for attachment in attachments:
    print(f"Attachment: {attachment['filename']}")
    print(f"Size: {attachment['size']} bytes")
    print(f"URL: {attachment['content']}")
```

## Examples

### Example 1: Create Epic with Child Issues

```python
from temet_jira import JiraClient, EpicBuilder, IssueBuilder

client = JiraClient()

# Create epic
epic_builder = EpicBuilder(
    title="User Authentication System",
    priority="P1",
    services="Backend, Frontend"
)
epic_builder.add_description("Complete authentication system implementation")

epic = client.create_issue({
    "project": {"key": "PROJ"},
    "summary": "User Authentication System",
    "issuetype": {"name": "Epic"},
    "description": epic_builder.build()
})

print(f"Created epic: {epic['key']}")

# Create child issues
tasks = [
    "Implement OAuth2 flow",
    "Add session management",
    "Create user profile endpoint",
    "Add JWT token handling"
]

epic_link_field = client.get_epic_link_field()

for task in tasks:
    issue_builder = IssueBuilder(title=task, epic_key=epic['key'])

    issue = client.create_issue({
        "project": {"key": "PROJ"},
        "summary": task,
        "issuetype": {"name": "Task"},
        "description": issue_builder.build(),
        epic_link_field: epic['key']
    })

    print(f"  Created task: {issue['key']} - {task}")
```

### Example 2: Generate Sprint Report

```python
from temet_jira import JiraClient
import csv

client = JiraClient()

# Get sprint issues
issues = client.search_issues(
    "sprint in openSprints()",
    max_results=None
)

# Group by status
by_status = {}
for issue in issues:
    status = issue['fields']['status']['name']
    if status not in by_status:
        by_status[status] = []
    by_status[status].append(issue)

# Write report
with open("sprint_report.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Status", "Key", "Summary", "Assignee"])

    for status, issues in by_status.items():
        for issue in issues:
            assignee = issue['fields']['assignee']
            assignee_name = assignee['displayName'] if assignee else "Unassigned"

            writer.writerow([
                status,
                issue['key'],
                issue['fields']['summary'],
                assignee_name
            ])

print("Sprint report generated: sprint_report.csv")
```

### Example 3: Workflow Bottleneck Analysis

```python
from temet_jira import JiraClient
from temet_jira.analysis import StateDurationAnalyzer
from collections import defaultdict

client = JiraClient()
analyzer = StateDurationAnalyzer()

# Get completed issues from last month
issues = client.search_issues(
    "project = PROJ AND status = Done AND resolved >= -30d",
    expand=["changelog"],
    max_results=None
)

# Analyze durations
results = analyzer.analyze_issues(issues)

# Calculate average time in each state
state_totals = defaultdict(lambda: {"total": 0, "count": 0})

for issue_key, durations in results.items():
    for duration in durations:
        state_totals[duration.state]["total"] += duration.duration_business_hours
        state_totals[duration.state]["count"] += 1

# Print bottlenecks
print("Average time in each state (business hours):")
print("-" * 50)

for state, data in sorted(state_totals.items(), key=lambda x: x[1]["total"] / x[1]["count"], reverse=True):
    avg = data["total"] / data["count"]
    print(f"{state:20s}: {avg:6.1f} hours ({data['count']} issues)")
```

## See Also

- [CLI Reference](../reference/cli_reference.md) - Command-line interface
- [Usage Guide](usage_guide.md) - Common workflows and examples
- [ADF Reference](../reference/adf_reference_guide.md) - Document formatting
- [Setup Guide](jira_setup.md) - Initial configuration
