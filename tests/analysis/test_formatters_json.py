"""Tests for the JSON formatter function."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from temet_jira.analysis.formatters import format_as_json


class TestFormatAsJson:
    """Test suite for format_as_json function."""

    def test_empty_list_returns_empty_json_array(self):
        """Test that an empty list returns a valid empty JSON array."""
        result = format_as_json([])
        assert result == "[]"
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == []

    def test_single_issue_basic_structure(self):
        """Test formatting a single issue with basic structure."""
        issues = [
            {
                "key": "PROJ-123",
                "id": "10001",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert len(parsed) == 1
        assert parsed[0]["key"] == "PROJ-123"
        assert parsed[0]["fields"]["summary"] == "Test issue"
        assert parsed[0]["fields"]["status"]["name"] == "Open"

    def test_multiple_issues(self):
        """Test formatting multiple issues."""
        issues = [
            {"key": "PROJ-1", "fields": {"summary": "Issue 1"}},
            {"key": "PROJ-2", "fields": {"summary": "Issue 2"}},
            {"key": "PROJ-3", "fields": {"summary": "Issue 3"}},
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert len(parsed) == 3
        assert all(issue["key"] in ["PROJ-1", "PROJ-2", "PROJ-3"] for issue in parsed)

    def test_nested_data_structures(self):
        """Test handling of deeply nested data structures."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {
                            "id": 4,
                            "key": "indeterminate",
                            "name": "In Progress",
                            "colorName": "yellow",
                        },
                    },
                    "assignee": {
                        "displayName": "John Doe",
                        "emailAddress": "john@example.com",
                        "avatarUrls": {
                            "48x48": "https://example.com/avatar.png",
                            "24x24": "https://example.com/avatar-small.png",
                        },
                    },
                    "components": [
                        {"name": "Backend", "id": "10001"},
                        {"name": "Frontend", "id": "10002"},
                    ],
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        # Verify nested structure is preserved
        status = parsed[0]["fields"]["status"]
        assert status["statusCategory"]["colorName"] == "yellow"
        assert (
            parsed[0]["fields"]["assignee"]["avatarUrls"]["48x48"]
            == "https://example.com/avatar.png"
        )
        assert len(parsed[0]["fields"]["components"]) == 2

    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized to ISO format."""
        now = datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "created": now,
                    "updated": datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
                    "duedate": datetime(2024, 2, 1, 0, 0, 0),  # No timezone
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["created"] == "2024-01-15T14:30:45+00:00"
        assert parsed[0]["fields"]["updated"] == "2024-01-16T10:00:00+00:00"
        # Naive datetime should still be serialized
        assert "2024-02-01" in parsed[0]["fields"]["duedate"]

    def test_special_types_serialization(self):
        """Test serialization of special Python types."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "storyPoints": Decimal("3.5"),
                    "progress": 0.75,
                    "isBlocked": True,
                    "blockedReason": None,
                    "tags": {"backend", "urgent"},  # Set
                    "priority": 1,
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["storyPoints"] == 3.5
        assert parsed[0]["fields"]["progress"] == 0.75
        assert parsed[0]["fields"]["isBlocked"] is True
        assert parsed[0]["fields"]["blockedReason"] is None
        # Set should be converted to list
        assert isinstance(parsed[0]["fields"]["tags"], list)
        assert set(parsed[0]["fields"]["tags"]) == {"backend", "urgent"}

    def test_custom_indentation(self):
        """Test custom indentation levels."""
        issues = [{"key": "PROJ-1", "fields": {"summary": "Test"}}]

        # Test with no indentation (compact)
        result_compact = format_as_json(issues, indent=None)
        assert "\n" not in result_compact
        assert result_compact == json.dumps(issues)

        # Test with 4-space indentation
        result_4 = format_as_json(issues, indent=4)
        lines = result_4.split("\n")
        # Check that nested content is indented with 4 spaces
        assert any("    " in line for line in lines)

        # Test with 2-space indentation (default)
        result_2 = format_as_json(issues, indent=2)
        lines = result_2.split("\n")
        # Check that nested content is indented with 2 spaces
        assert any("  " in line for line in lines)

    def test_sort_keys_parameter(self):
        """Test that sort_keys parameter orders dictionary keys."""
        issues = [
            {
                "key": "PROJ-123",
                "id": "10001",
                "fields": {
                    "summary": "Test",
                    "assignee": {"name": "John"},
                    "status": {"name": "Open"},
                },
            }
        ]

        result = format_as_json(issues, sort_keys=True)

        # Keys should appear in alphabetical order in the JSON string
        field_positions = {
            "assignee": result.find('"assignee"'),
            "status": result.find('"status"'),
            "summary": result.find('"summary"'),
        }

        # Verify alphabetical ordering
        assert field_positions["assignee"] < field_positions["status"]
        assert field_positions["status"] < field_positions["summary"]

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Fix unicode: 你好世界 🚀",
                    "description": "Contains \"quotes\" and 'apostrophes'",
                    "customField": "Line1\nLine2\tTabbed",
                    "path": "C:\\Users\\John\\Documents",
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["summary"] == "Fix unicode: 你好世界 🚀"
        assert (
            parsed[0]["fields"]["description"]
            == "Contains \"quotes\" and 'apostrophes'"
        )
        assert "Line1\nLine2\tTabbed" in parsed[0]["fields"]["customField"]
        assert parsed[0]["fields"]["path"] == "C:\\Users\\John\\Documents"

    def test_lists_and_arrays(self):
        """Test proper handling of lists and arrays in data."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "labels": ["backend", "urgent", "bug"],
                    "fixVersions": [],
                    "watchers": [
                        {"name": "User1", "email": "user1@example.com"},
                        {"name": "User2", "email": "user2@example.com"},
                    ],
                    "attachments": None,
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["labels"] == ["backend", "urgent", "bug"]
        assert parsed[0]["fields"]["fixVersions"] == []
        assert len(parsed[0]["fields"]["watchers"]) == 2
        assert parsed[0]["fields"]["attachments"] is None

    def test_custom_object_with_dict_method(self):
        """Test serialization of custom objects that have __dict__ method."""

        class CustomStatus:
            def __init__(self, name, status_id):
                self.name = name
                self.id = status_id

        status = CustomStatus("Open", 1)
        issues = [{"key": "PROJ-123", "fields": {"status": status}}]

        result = format_as_json(issues)
        parsed = json.loads(result)

        # Should serialize using object's __dict__
        assert parsed[0]["fields"]["status"]["name"] == "Open"
        assert parsed[0]["fields"]["status"]["id"] == 1

    def test_non_serializable_fallback(self):
        """Test that non-serializable objects fall back to string representation."""

        class NonSerializable:
            def __repr__(self):
                return "<NonSerializable object>"

        issues = [{"key": "PROJ-123", "fields": {"customObject": NonSerializable()}}]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["customObject"] == "<NonSerializable object>"

    def test_circular_reference_handling(self):
        """Test that circular references are handled gracefully."""
        # Create a circular reference
        issue = {"key": "PROJ-123", "fields": {}}
        issue["fields"]["self"] = issue  # Circular reference

        # Should not raise an exception but handle gracefully
        with pytest.raises(ValueError, match="Circular reference detected"):
            format_as_json([issue])

    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "largeInt": 9999999999999999999999,
                    "largeFloat": 1.7976931348623157e308,  # Near max float
                    "negativeInf": float("-inf"),
                    "positiveInf": float("inf"),
                    "notANumber": float("nan"),
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        assert parsed[0]["fields"]["largeInt"] == 9999999999999999999999
        assert parsed[0]["fields"]["largeFloat"] == 1.7976931348623157e308
        # Infinity and NaN should be handled - converted to None
        assert parsed[0]["fields"]["negativeInf"] is None
        assert parsed[0]["fields"]["positiveInf"] is None
        assert parsed[0]["fields"]["notANumber"] is None

    def test_bytes_serialization(self):
        """Test serialization of bytes objects."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "binaryData": b"Hello World",
                    "emptyBytes": b"",
                    "unicodeBytes": "Hello 世界".encode(),
                },
            }
        ]

        result = format_as_json(issues)
        parsed = json.loads(result)

        # Bytes should be decoded or converted to string
        assert isinstance(parsed[0]["fields"]["binaryData"], str)
        assert (
            "Hello World" in parsed[0]["fields"]["binaryData"]
            or parsed[0]["fields"]["binaryData"] == "b'Hello World'"
        )

    def test_performance_with_large_dataset(self):
        """Test performance with a large number of issues."""
        # Create 1000 issues
        issues = [
            {
                "key": f"PROJ-{i}",
                "id": str(10000 + i),
                "fields": {
                    "summary": f"Issue {i}",
                    "description": f"Description for issue {i}" * 10,
                    "status": {"name": "Open", "id": i % 5},
                    "labels": [f"label{j}" for j in range(5)],
                },
            }
            for i in range(1000)
        ]

        # Should complete without error
        result = format_as_json(issues)
        parsed = json.loads(result)

        assert len(parsed) == 1000
        assert parsed[0]["key"] == "PROJ-0"
        assert parsed[999]["key"] == "PROJ-999"
