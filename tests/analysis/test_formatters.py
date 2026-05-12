"""Tests for Jira data formatters."""

import csv
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures.jira_data import (  # noqa: E402
    EPIC_ISSUE,
    MINIMAL_ISSUE,
    SAMPLE_ISSUE,
)

from temet_jira.analysis.formatters import (  # noqa: E402
    format_as_csv,
)


class TestFormatAsCSV:
    """Test suite for CSV formatting functionality."""

    def test_empty_list_returns_empty_string(self):
        """Test that empty issue list returns empty string."""
        result = format_as_csv([])
        assert result == ""

    def test_single_issue_basic_fields(self):
        """Test CSV formatting with a single issue containing basic fields."""
        issues = [
            {
                "key": "PROJ-123",
                "id": "10001",
                "fields": {
                    "summary": "Fix login bug",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["key"] == "PROJ-123"
        assert rows[0]["id"] == "10001"
        assert rows[0]["fields.summary"] == "Fix login bug"
        assert rows[0]["fields.status.name"] == "In Progress"
        assert rows[0]["fields.priority.name"] == "High"

    def test_nested_fields_flattening(self):
        """Test that nested fields are properly flattened with dot notation."""
        issues = [
            {
                "key": "PROJ-456",
                "fields": {
                    "summary": "Test issue",
                    "assignee": {
                        "displayName": "John Doe",
                        "emailAddress": "john@example.com",
                        "accountId": "user123",
                    },
                    "reporter": {
                        "displayName": "Jane Smith",
                        "emailAddress": "jane@example.com",
                    },
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.assignee.displayName"] == "John Doe"
        assert row["fields.assignee.emailAddress"] == "john@example.com"
        assert row["fields.assignee.accountId"] == "user123"
        assert row["fields.reporter.displayName"] == "Jane Smith"
        assert row["fields.reporter.emailAddress"] == "jane@example.com"

    def test_multi_value_fields(self):
        """Test that multi-value fields like labels and components are handled."""
        issues = [
            {
                "key": "PROJ-789",
                "fields": {
                    "summary": "Multi-value test",
                    "labels": ["bug", "critical", "security"],
                    "components": [
                        {"name": "Backend", "id": "1"},
                        {"name": "API", "id": "2"},
                    ],
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        # Multi-value fields should be semicolon-separated
        assert row["fields.labels"] == "bug;critical;security"
        assert row["fields.components"] == "Backend;API"

    def test_missing_fields_handled(self):
        """Test that missing fields are handled gracefully with empty strings."""
        issues = [
            {
                "key": "PROJ-001",
                "fields": {"summary": "Issue with missing fields"},
            },
            {
                "key": "PROJ-002",
                "fields": {
                    "summary": "Issue with all fields",
                    "assignee": {"displayName": "Bob"},
                    "priority": {"name": "Low"},
                },
            },
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 2
        # First issue should have empty values for missing fields
        assert rows[0]["key"] == "PROJ-001"
        assert rows[0]["fields.assignee.displayName"] == ""
        assert rows[0]["fields.priority.name"] == ""

        # Second issue should have values
        assert rows[1]["key"] == "PROJ-002"
        assert rows[1]["fields.assignee.displayName"] == "Bob"
        assert rows[1]["fields.priority.name"] == "Low"

    def test_csv_injection_protection(self):
        """Test that CSV injection attempts are neutralized."""
        issues = [
            {
                "key": "PROJ-999",
                "fields": {
                    "summary": "=1+1",  # Excel formula injection
                    "description": "+1+1",  # Plus formula
                    "comment": "-1+1",  # Minus formula
                    "custom": "@SUM(A1:A10)",  # At formula
                    "normal": "Regular text",
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        # Formulas should be prefixed with single quote
        assert row["fields.summary"] == "'=1+1"
        assert row["fields.description"] == "'+1+1"
        assert row["fields.comment"] == "'-1+1"
        assert row["fields.custom"] == "'@SUM(A1:A10)"
        assert row["fields.normal"] == "Regular text"

    def test_custom_delimiter(self):
        """Test that custom delimiter is used when specified."""
        issues = [
            {
                "key": "PROJ-100",
                "fields": {"summary": "Test with pipe delimiter"},
            }
        ]

        result = format_as_csv(issues, delimiter="|")
        lines = result.strip().split("\n")

        # Header should use pipe delimiter
        assert "|" in lines[0]
        assert "," not in lines[0]
        # Data row should use pipe delimiter
        assert "|" in lines[1]
        assert "," not in lines[1]

    def test_no_headers_option(self):
        """Test that headers can be excluded."""
        issues = [
            {
                "key": "PROJ-200",
                "fields": {"summary": "No headers test"},
            }
        ]

        result = format_as_csv(issues, include_headers=False)
        lines = result.strip().split("\n")

        # Should only have one line (data, no header)
        assert len(lines) == 1
        assert "PROJ-200" in lines[0]
        assert "key" not in lines[0]  # No header row

    def test_complex_nested_structure(self):
        """Test handling of deeply nested structures."""
        issues = [
            {
                "key": "PROJ-300",
                "fields": {
                    "project": {
                        "key": "PROJ",
                        "name": "Project Name",
                        "projectType": {
                            "key": "software",
                            "displayName": "Software Project",
                        },
                    },
                    "issuetype": {
                        "name": "Bug",
                        "subtask": False,
                        "hierarchyLevel": 0,
                    },
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.project.key"] == "PROJ"
        assert row["fields.project.name"] == "Project Name"
        assert row["fields.project.projectType.key"] == "software"
        assert row["fields.project.projectType.displayName"] == "Software Project"
        assert row["fields.issuetype.name"] == "Bug"
        assert row["fields.issuetype.subtask"] == "False"
        assert row["fields.issuetype.hierarchyLevel"] == "0"

    def test_null_and_none_values(self):
        """Test that null/None values are handled as empty strings."""
        issues = [
            {
                "key": "PROJ-400",
                "fields": {
                    "summary": "Test nulls",
                    "assignee": None,
                    "priority": {"name": None},
                    "labels": None,
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.assignee"] == ""
        assert row["fields.priority.name"] == ""
        assert row["fields.labels"] == ""

    def test_special_characters_in_values(self):
        """Test that special characters in values are properly escaped."""
        issues = [
            {
                "key": "PROJ-500",
                "fields": {
                    "summary": 'Summary with "quotes"',
                    "description": "Text with, comma",
                    "comment": "Text with\nnewline",
                },
            }
        ]

        result = format_as_csv(issues)

        # Parse with csv reader to ensure proper escaping
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.summary"] == 'Summary with "quotes"'
        assert row["fields.description"] == "Text with, comma"
        assert row["fields.comment"] == "Text with\nnewline"

    def test_multiple_issues_consistent_columns(self):
        """Test that multiple issues produce consistent columns."""
        issues = [
            {
                "key": "PROJ-601",
                "fields": {
                    "summary": "First issue",
                    "assignee": {"displayName": "Alice"},
                },
            },
            {
                "key": "PROJ-602",
                "fields": {
                    "summary": "Second issue",
                    "priority": {"name": "High"},
                },
            },
            {
                "key": "PROJ-603",
                "fields": {
                    "summary": "Third issue",
                    "labels": ["bug"],
                },
            },
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 3

        # All rows should have the same keys (columns)
        keys = set(rows[0].keys())
        for row in rows:
            assert set(row.keys()) == keys

        # Check specific values
        assert rows[0]["fields.assignee.displayName"] == "Alice"
        assert rows[0]["fields.priority.name"] == ""  # Missing in first issue
        assert rows[1]["fields.assignee.displayName"] == ""  # Missing in second issue
        assert rows[1]["fields.priority.name"] == "High"
        assert rows[2]["fields.labels"] == "bug"

    def test_boolean_values(self):
        """Test that boolean values are properly converted to strings."""
        issues = [
            {
                "key": "PROJ-700",
                "fields": {
                    "resolved": True,
                    "subtask": False,
                    "flagged": True,
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.resolved"] == "True"
        assert row["fields.subtask"] == "False"
        assert row["fields.flagged"] == "True"

    def test_numeric_values(self):
        """Test that numeric values are properly converted to strings."""
        issues = [
            {
                "key": "PROJ-800",
                "fields": {
                    "storyPoints": 5,
                    "timeEstimate": 3.5,
                    "votesCount": 0,
                    "watchersCount": 10,
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.storyPoints"] == "5"
        assert row["fields.timeEstimate"] == "3.5"
        assert row["fields.votesCount"] == "0"
        assert row["fields.watchersCount"] == "10"

    def test_empty_arrays(self):
        """Test that empty arrays are handled as empty strings."""
        issues = [
            {
                "key": "PROJ-900",
                "fields": {
                    "labels": [],
                    "components": [],
                    "fixVersions": [],
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.labels"] == ""
        assert row["fields.components"] == ""
        assert row["fields.fixVersions"] == ""

    def test_mixed_array_types(self):
        """Test arrays containing different types of objects."""
        issues = [
            {
                "key": "PROJ-1000",
                "fields": {
                    "fixVersions": [
                        {"name": "1.0", "released": True},
                        {"name": "2.0", "released": False},
                    ],
                    "attachments": [
                        {"filename": "screenshot.png", "size": 12345},
                        {"filename": "log.txt", "size": 54321},
                    ],
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        # Complex objects in arrays should be simplified
        assert row["fields.fixVersions"] == "1.0;2.0"
        assert row["fields.attachments"] == "screenshot.png;log.txt"

    def test_deep_nesting_max_depth(self):
        """Test that very deeply nested structures are handled with max depth."""
        issues = [
            {
                "key": "PROJ-1100",
                "fields": {
                    "level1": {
                        "level2": {
                            "level3": {
                                "level4": {"level5": {"level6": {"value": "Too deep"}}}
                            }
                        }
                    }
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        # Should flatten up to max depth (5 by default)
        # At depth 5, the remaining structure is stringified
        assert "fields.level1.level2.level3.level4" in rows[0]
        assert "level5" in rows[0]["fields.level1.level2.level3.level4"]

    def test_date_and_datetime_fields(self):
        """Test that date and datetime fields are properly formatted."""
        from datetime import date, datetime

        issues = [
            {
                "key": "PROJ-1200",
                "fields": {
                    "created": datetime(2023, 1, 15, 10, 30, 45),
                    "dueDate": date(2023, 2, 1),
                    "updated": "2023-01-20T15:45:00Z",  # String date
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert "2023-01-15" in row["fields.created"]  # ISO format
        assert row["fields.dueDate"] == "2023-02-01"
        assert row["fields.updated"] == "2023-01-20T15:45:00Z"

    def test_decimal_values(self):
        """Test that Decimal values are properly handled."""
        from decimal import Decimal

        issues = [
            {
                "key": "PROJ-1300",
                "fields": {
                    "price": Decimal("99.99"),
                    "tax": Decimal("8.25"),
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.price"] == "99.99"
        assert row["fields.tax"] == "8.25"

    def test_array_with_mixed_types(self):
        """Test arrays containing mixed primitive types."""
        issues = [
            {
                "key": "PROJ-1400",
                "fields": {
                    "mixedArray": [1, "two", 3.0, True, None],
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["fields.mixedArray"] == "1;two;3.0;True;None"

    def test_dict_without_common_fields(self):
        """Test array of dicts without common field names."""
        issues = [
            {
                "key": "PROJ-1500",
                "fields": {
                    "customObjects": [
                        {"id": "1", "type": "A"},
                        {"code": "2", "category": "B"},
                        {"value": "3"},
                    ],
                },
            }
        ]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        # Should extract first string value from each dict
        assert "1" in row["fields.customObjects"]
        assert "2" in row["fields.customObjects"]
        assert "3" in row["fields.customObjects"]

    def test_real_jira_fixture_data(self):
        """Test formatting with real Jira fixture data."""
        issues = [SAMPLE_ISSUE, MINIMAL_ISSUE, EPIC_ISSUE]

        result = format_as_csv(issues)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 3

        # Check SAMPLE_ISSUE fields
        assert rows[0]["key"] == "PROJ-123"
        assert rows[0]["fields.summary"] == "Sample Jira Issue"
        assert rows[0]["fields.status.name"] == "To Do"
        assert rows[0]["fields.assignee.displayName"] == "John Doe"
        assert rows[0]["fields.labels"] == "urgent;bug-fix"
        assert rows[0]["fields.components"] == "Authentication"

        # Check MINIMAL_ISSUE fields
        assert rows[1]["key"] == "PROJ-124"
        assert rows[1]["fields.summary"] == "Minimal Issue"
        assert rows[1]["fields.status.name"] == "In Progress"
        assert rows[1]["fields.assignee.displayName"] == ""  # Missing field

        # Check EPIC_ISSUE fields
        assert rows[2]["key"] == "PROJ-470"
        assert rows[2]["fields.summary"] == "Platform Enhancement Implementation"
        assert rows[2]["fields.priority.name"] == "High"
        assert rows[2]["fields.assignee.emailAddress"] == "epic.owner@example.com"
