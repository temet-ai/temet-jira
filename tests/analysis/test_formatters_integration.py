"""Integration tests for the formatters module."""

import json
from datetime import UTC, datetime

from temet_jira.analysis.formatters import format_as_json


def test_format_real_jira_response():
    """Test formatting a realistic Jira API response."""
    # Simulate a realistic Jira API response
    jira_response = [
        {
            "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
            "id": "10001",
            "self": "https://jira.example.com/rest/api/3/issue/10001",
            "key": "PROJ-123",
            "fields": {
                "issuetype": {
                    "self": "https://jira.example.com/rest/api/3/issuetype/10001",
                    "id": "10001",
                    "description": "A task that needs to be done.",
                    "iconUrl": "https://jira.example.com/images/icons/issuetypes/task.png",
                    "name": "Task",
                    "subtask": False,
                    "hierarchyLevel": 0,
                },
                "timespent": None,
                "timeoriginalestimate": None,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"text": "This is a description with ", "type": "text"},
                                {
                                    "text": "bold text",
                                    "type": "text",
                                    "marks": [{"type": "strong"}],
                                },
                            ],
                        }
                    ],
                },
                "project": {
                    "self": "https://jira.example.com/rest/api/3/project/10000",
                    "id": "10000",
                    "key": "PROJ",
                    "name": "Project Name",
                    "projectTypeKey": "software",
                    "simplified": False,
                    "avatarUrls": {
                        "48x48": "https://jira.example.com/secure/projectavatar?pid=10000&avatarId=10200",
                        "24x24": "https://jira.example.com/secure/projectavatar?size=small&pid=10000&avatarId=10200",
                        "16x16": "https://jira.example.com/secure/projectavatar?size=xsmall&pid=10000&avatarId=10200",
                        "32x32": "https://jira.example.com/secure/projectavatar?size=medium&pid=10000&avatarId=10200",
                    },
                },
                "fixVersions": [],
                "aggregatetimespent": None,
                "resolution": None,
                "timetracking": {},
                "customfield_10006": 3.0,  # Story points
                "customfield_10007": None,
                "attachment": [],
                "aggregatetimeestimate": None,
                "resolutiondate": None,
                "workratio": -1,
                "summary": "Implement new feature for customer portal",
                "lastViewed": "2024-01-15T10:30:00.000+0000",
                "watches": {
                    "self": "https://jira.example.com/rest/api/3/issue/PROJ-123/watchers",
                    "watchCount": 2,
                    "isWatching": True,
                },
                "creator": {
                    "self": "https://jira.example.com/rest/api/3/user?accountId=123456",
                    "accountId": "123456",
                    "emailAddress": "john.doe@example.com",
                    "avatarUrls": {
                        "48x48": "https://avatar.example.com/123456?d=mm&s=48",
                        "24x24": "https://avatar.example.com/123456?d=mm&s=24",
                        "16x16": "https://avatar.example.com/123456?d=mm&s=16",
                        "32x32": "https://avatar.example.com/123456?d=mm&s=32",
                    },
                    "displayName": "John Doe",
                    "active": True,
                    "timeZone": "America/New_York",
                    "accountType": "atlassian",
                },
                "subtasks": [],
                "created": datetime(2024, 1, 10, 9, 15, 30, tzinfo=UTC),
                "reporter": {
                    "self": "https://jira.example.com/rest/api/3/user?accountId=123456",
                    "accountId": "123456",
                    "emailAddress": "john.doe@example.com",
                    "displayName": "John Doe",
                    "active": True,
                    "timeZone": "America/New_York",
                    "accountType": "atlassian",
                },
                "aggregateprogress": {"progress": 0, "total": 0},
                "priority": {
                    "self": "https://jira.example.com/rest/api/3/priority/3",
                    "iconUrl": "https://jira.example.com/images/icons/priorities/medium.svg",
                    "name": "Medium",
                    "id": "3",
                },
                "labels": ["backend", "customer-facing", "Q1-2024"],
                "environment": None,
                "timeestimate": None,
                "aggregatetimeoriginalestimate": None,
                "versions": [],
                "duedate": None,
                "progress": {"progress": 0, "total": 0},
                "comment": {
                    "comments": [],
                    "self": "https://jira.example.com/rest/api/3/issue/10001/comment",
                    "maxResults": 0,
                    "total": 0,
                    "startAt": 0,
                },
                "issuelinks": [],
                "assignee": {
                    "self": "https://jira.example.com/rest/api/3/user?accountId=789012",
                    "accountId": "789012",
                    "emailAddress": "jane.smith@example.com",
                    "displayName": "Jane Smith",
                    "active": True,
                    "timeZone": "Europe/London",
                    "accountType": "atlassian",
                },
                "updated": datetime(2024, 1, 15, 14, 45, 0, tzinfo=UTC),
                "status": {
                    "self": "https://jira.example.com/rest/api/3/status/10001",
                    "description": "The issue is being actively worked on",
                    "iconUrl": "https://jira.example.com/images/icons/statuses/inprogress.png",
                    "name": "In Progress",
                    "id": "10001",
                    "statusCategory": {
                        "self": "https://jira.example.com/rest/api/3/statuscategory/4",
                        "id": 4,
                        "key": "indeterminate",
                        "colorName": "yellow",
                        "name": "In Progress",
                    },
                },
                "components": [
                    {
                        "self": "https://jira.example.com/rest/api/3/component/10000",
                        "id": "10000",
                        "name": "Backend Services",
                        "description": "Backend API and services",
                    },
                    {
                        "self": "https://jira.example.com/rest/api/3/component/10001",
                        "id": "10001",
                        "name": "Customer Portal",
                        "description": "Customer-facing web portal",
                    },
                ],
                "security": None,
                "statuscategorychangedate": "2024-01-12T11:30:00.000+0000",
                "issuerestriction": {"issuerestrictions": {}, "shouldDisplay": False},
                "worklog": {"startAt": 0, "maxResults": 20, "total": 0, "worklogs": []},
            },
        },
        {
            "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
            "id": "10002",
            "self": "https://jira.example.com/rest/api/3/issue/10002",
            "key": "PROJ-124",
            "fields": {
                "summary": "Fix bug in authentication module",
                "status": {
                    "self": "https://jira.example.com/rest/api/3/status/10002",
                    "name": "To Do",
                    "id": "10002",
                },
                "priority": {
                    "self": "https://jira.example.com/rest/api/3/priority/2",
                    "name": "High",
                    "id": "2",
                },
                "assignee": None,
                "created": datetime(2024, 1, 14, 15, 0, 0, tzinfo=UTC),
                "updated": datetime(2024, 1, 14, 15, 0, 0, tzinfo=UTC),
                "labels": ["bug", "security", "authentication"],
                "customfield_10006": 5.0,  # Story points
            },
        },
    ]

    # Format the response
    result = format_as_json(jira_response, indent=2)

    # Verify it's valid JSON
    parsed = json.loads(result)

    # Verify structure is preserved
    assert len(parsed) == 2
    assert parsed[0]["key"] == "PROJ-123"
    assert parsed[1]["key"] == "PROJ-124"

    # Verify datetime conversion
    assert parsed[0]["fields"]["created"] == "2024-01-10T09:15:30+00:00"
    assert parsed[0]["fields"]["updated"] == "2024-01-15T14:45:00+00:00"

    # Verify nested structures
    assert parsed[0]["fields"]["status"]["statusCategory"]["colorName"] == "yellow"
    assert len(parsed[0]["fields"]["components"]) == 2
    assert parsed[0]["fields"]["labels"] == ["backend", "customer-facing", "Q1-2024"]

    # Verify None values are preserved
    assert parsed[0]["fields"]["duedate"] is None
    assert parsed[1]["fields"]["assignee"] is None

    # Verify numbers are preserved
    assert parsed[0]["fields"]["customfield_10006"] == 3.0
    assert parsed[1]["fields"]["customfield_10006"] == 5.0

    # Print a sample of the output for manual verification
    print("\nSample of formatted JSON output:")
    print(result[:500] + "..." if len(result) > 500 else result)
