"""Integration tests for StateDurationAnalyzer with realistic Jira data."""

from datetime import UTC, datetime

import pytest

from temet_jira.analysis.state_analyzer import (
    StateDurationAnalyzer,
)


class TestStateAnalyzerIntegration:
    """Integration tests with realistic Jira issue data."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_complex_workflow_with_backtracking(self, analyzer):
        """Test handling of complex workflow with status moving backwards."""
        issue = {
            "key": "PROD-456",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0000",
                        "author": {"displayName": "Dev Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-03T11:00:00.000+0000",
                        "author": {"displayName": "QA Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Testing",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-04T14:00:00.000+0000",
                        "author": {"displayName": "QA Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Testing",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-05T16:00:00.000+0000",
                        "author": {"displayName": "Dev Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Testing",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-06T09:00:00.000+0000",
                        "author": {"displayName": "QA Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Testing",
                                "toString": "Done",
                            }
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 6

        # Verify the complete flow including backtracking
        expected_flow = [
            ("To Do", None),  # Initial
            ("In Progress", "To Do"),  # Dev starts
            ("Testing", "In Progress"),  # QA starts
            ("In Progress", "Testing"),  # Back to dev (bug found)
            ("Testing", "In Progress"),  # Back to QA
            ("Done", "Testing"),  # Complete
        ]

        for i, (expected_to, expected_from) in enumerate(expected_flow):
            assert transitions[i].to_state == expected_to
            assert transitions[i].from_state == expected_from

    def test_rapid_transitions_same_day(self, analyzer):
        """Test handling of multiple transitions on the same day."""
        issue = {
            "key": "HOTFIX-789",
            "fields": {
                "created": "2024-01-15T08:00:00.000+0000",
                "status": {"name": "Deployed"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-15T08:30:00.000+0000",
                        "author": {"displayName": "Emergency Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-15T09:00:00.000+0000",
                        "author": {"displayName": "Emergency Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Code Review",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-15T09:30:00.000+0000",
                        "author": {"displayName": "Senior Dev"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Code Review",
                                "toString": "Testing",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-15T10:00:00.000+0000",
                        "author": {"displayName": "QA Team"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Testing",
                                "toString": "Ready to Deploy",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-15T10:30:00.000+0000",
                        "author": {"displayName": "DevOps"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Ready to Deploy",
                                "toString": "Deployed",
                            }
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 6

        # All transitions should be on the same day
        for transition in transitions:
            assert transition.timestamp.date() == datetime(2024, 1, 15).date()

        # Verify the rapid progression
        assert transitions[-1].to_state == "Deployed"
        # Total time from creation to deployment: 2.5 hours
        time_diff = transitions[-1].timestamp - transitions[0].timestamp
        assert time_diff.total_seconds() == 2.5 * 3600

    def test_multiple_field_changes_in_single_history(self, analyzer):
        """Test extraction when multiple fields change in single history entry."""
        issue = {
            "key": "FEAT-321",
            "fields": {
                "created": "2024-02-01T10:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-02-02T11:00:00.000+0000",
                        "author": {"displayName": "Project Manager"},
                        "items": [
                            {
                                "field": "priority",
                                "fromString": "Low",
                                "toString": "High",
                            },
                            {
                                "field": "assignee",
                                "fromString": None,
                                "toString": "john.doe",
                            },
                            {
                                "field": "status",
                                "fromString": "Backlog",
                                "toString": "To Do",
                            },
                            {"field": "labels", "fromString": "", "toString": "urgent"},
                        ],
                    },
                    {
                        "created": "2024-02-03T14:00:00.000+0000",
                        "author": {"displayName": "Developer"},
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            },
                            {
                                "field": "timeestimate",
                                "fromString": None,
                                "toString": "3600",
                            },
                        ],
                    },
                    {
                        "created": "2024-02-05T16:00:00.000+0000",
                        "author": {"displayName": "Developer"},
                        "items": [
                            {
                                "field": "resolution",
                                "fromString": None,
                                "toString": "Fixed",
                            },
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Done",
                            },
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        # Should only extract status transitions, ignoring other field changes
        assert len(transitions) == 4

        status_progression = [t.to_state for t in transitions]
        assert status_progression == ["Backlog", "To Do", "In Progress", "Done"]

    def test_real_world_jira_data_format(self, analyzer):
        """Test with data matching actual Jira API response format."""
        issue = {
            "expand": "operations,versionedRepresentations,editmeta,changelog",
            "id": "123456",
            "self": "https://jira.example.com/rest/api/2/issue/123456",
            "key": "PROJ-470",
            "fields": {
                "created": "2023-11-15T10:23:45.123+0000",
                "updated": "2024-01-20T15:30:22.456+0000",
                "status": {
                    "self": "https://jira.example.com/rest/api/2/status/10001",
                    "description": "The issue is considered finished",
                    "iconUrl": "https://jira.example.com/images/icons/statuses/closed.png",
                    "name": "Closed",
                    "id": "10001",
                    "statusCategory": {
                        "self": "https://jira.example.com/rest/api/2/statuscategory/3",
                        "id": 3,
                        "key": "done",
                        "colorName": "green",
                        "name": "Done",
                    },
                },
                "summary": "Implement OAuth2 authentication flow",
                "description": "As a user, I want to authenticate using OAuth2...",
                "issuetype": {"id": "10002", "name": "Story", "subtask": False},
            },
            "changelog": {
                "startAt": 0,
                "maxResults": 20,
                "total": 15,
                "histories": [
                    {
                        "id": "654321",
                        "author": {
                            "self": "https://jira.example.com/rest/api/2/user?accountId=abc123",
                            "accountId": "abc123",
                            "emailAddress": "dev@example.com",
                            "avatarUrls": {},
                            "displayName": "John Developer",
                            "active": True,
                            "timeZone": "America/New_York",
                            "accountType": "atlassian",
                        },
                        "created": "2023-11-20T14:30:00.000+0000",
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "fieldId": "status",
                                "from": "1",
                                "fromString": "Open",
                                "to": "3",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "id": "654322",
                        "author": {
                            "self": "https://jira.example.com/rest/api/2/user?accountId=def456",
                            "accountId": "def456",
                            "displayName": "Jane QA",
                            "active": True,
                        },
                        "created": "2023-12-01T09:15:30.000+0000",
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "from": "3",
                                "fromString": "In Progress",
                                "to": "5",
                                "toString": "In Review",
                            }
                        ],
                    },
                    {
                        "id": "654323",
                        "author": {"displayName": "CI/CD Bot", "accountType": "app"},
                        "created": "2024-01-20T15:30:22.456+0000",
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "from": "5",
                                "fromString": "In Review",
                                "to": "10001",
                                "toString": "Closed",
                            }
                        ],
                    },
                ],
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 4

        # Check the complete workflow
        assert transitions[0].to_state == "Open"
        assert transitions[0].from_state is None
        assert transitions[0].author is None

        assert transitions[1].to_state == "In Progress"
        assert transitions[1].from_state == "Open"
        assert transitions[1].author == "John Developer"

        assert transitions[2].to_state == "In Review"
        assert transitions[2].from_state == "In Progress"
        assert transitions[2].author == "Jane QA"

        assert transitions[3].to_state == "Closed"
        assert transitions[3].from_state == "In Review"
        assert transitions[3].author == "CI/CD Bot"

        # Verify timestamps are parsed correctly
        for transition in transitions:
            assert transition.timestamp.tzinfo is not None

    def test_issue_with_no_transitions_stays_in_initial_state(self, analyzer):
        """Test issue that has never changed status."""
        issue = {
            "key": "NEW-001",
            "fields": {
                "created": "2024-01-20T12:00:00.000+0000",
                "status": {"name": "Open"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-20T12:30:00.000+0000",
                        "items": [
                            {
                                "field": "description",
                                "fromString": "",
                                "toString": "Added description",
                            },
                            {
                                "field": "priority",
                                "fromString": "Medium",
                                "toString": "High",
                            },
                        ],
                    },
                    {
                        "created": "2024-01-21T09:00:00.000+0000",
                        "items": [
                            {
                                "field": "assignee",
                                "fromString": None,
                                "toString": "alice@example.com",
                            }
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        # Should only have the initial state
        assert len(transitions) == 1
        assert transitions[0].from_state is None
        assert transitions[0].to_state == "Open"
        assert transitions[0].timestamp == datetime(2024, 1, 20, 12, 0, 0, tzinfo=UTC)
