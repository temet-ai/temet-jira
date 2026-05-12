"""Tests for the JSONL formatter function."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from temet_jira.analysis.formatters import format_as_jsonl


class TestFormatAsJsonl:
    """Test suite for format_as_jsonl function."""

    def test_empty_list_returns_empty_string(self):
        """Test that an empty list returns an empty string."""
        result = format_as_jsonl([])
        assert result == ""

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

        result = format_as_jsonl(issues)
        lines = result.split("\n")

        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["key"] == "PROJ-123"
        assert parsed["fields"]["summary"] == "Test issue"
        assert parsed["fields"]["status"]["name"] == "Open"

    def test_multiple_issues_one_per_line(self):
        """Test that multiple issues each get their own line."""
        issues = [
            {"key": "PROJ-1", "fields": {"summary": "Issue 1"}},
            {"key": "PROJ-2", "fields": {"summary": "Issue 2"}},
            {"key": "PROJ-3", "fields": {"summary": "Issue 3"}},
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")

        assert len(lines) == 3
        for i, line in enumerate(lines, 1):
            parsed = json.loads(line)
            assert parsed["key"] == f"PROJ-{i}"
            assert parsed["fields"]["summary"] == f"Issue {i}"

    def test_compact_format_no_indentation(self):
        """Test that JSONL uses compact format (no indentation/newlines within objects)."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {"summary": "Test", "status": {"name": "Open"}},
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")

        # Each line should be a single compact JSON object (no newlines within)
        assert len(lines) == 1
        # Should not contain multiple spaces or newlines
        assert "  " not in lines[0]  # No double spaces (indicating indentation)
        # Should be valid JSON
        parsed = json.loads(lines[0])
        assert parsed["key"] == "PROJ-123"

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
                    "components": [
                        {"name": "Backend", "id": "10001"},
                        {"name": "Frontend", "id": "10002"},
                    ],
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        # Verify nested structure is preserved
        status = parsed["fields"]["status"]
        assert status["statusCategory"]["colorName"] == "yellow"
        assert len(parsed["fields"]["components"]) == 2

    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized to ISO format."""
        now = datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "created": now,
                    "updated": datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        assert parsed["fields"]["created"] == "2024-01-15T14:30:45+00:00"
        assert parsed["fields"]["updated"] == "2024-01-16T10:00:00+00:00"

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
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        assert parsed["fields"]["storyPoints"] == 3.5
        assert parsed["fields"]["progress"] == 0.75
        assert parsed["fields"]["isBlocked"] is True
        assert parsed["fields"]["blockedReason"] is None
        # Set should be converted to list
        assert isinstance(parsed["fields"]["tags"], list)
        assert set(parsed["fields"]["tags"]) == {"backend", "urgent"}

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

        result = format_as_jsonl(issues, sort_keys=True)
        lines = result.split("\n")

        # Keys should appear in alphabetical order in the JSON string
        field_positions = {
            "assignee": lines[0].find('"assignee"'),
            "status": lines[0].find('"status"'),
            "summary": lines[0].find('"summary"'),
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
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        assert parsed["fields"]["summary"] == "Fix unicode: 你好世界 🚀"
        assert (
            parsed["fields"]["description"] == "Contains \"quotes\" and 'apostrophes'"
        )
        assert "Line1\nLine2\tTabbed" in parsed["fields"]["customField"]

    def test_circular_reference_handling(self):
        """Test that circular references are handled gracefully."""
        # Create a circular reference
        issue = {"key": "PROJ-123", "fields": {}}
        issue["fields"]["self"] = issue  # Circular reference

        # Should raise ValueError for circular reference
        with pytest.raises(ValueError, match="Circular reference detected"):
            format_as_jsonl([issue])

    def test_special_float_values(self):
        """Test handling of special float values (NaN, Infinity)."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "negativeInf": float("-inf"),
                    "positiveInf": float("inf"),
                    "notANumber": float("nan"),
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        # Infinity and NaN should be converted to None
        assert parsed["fields"]["negativeInf"] is None
        assert parsed["fields"]["positiveInf"] is None
        assert parsed["fields"]["notANumber"] is None

    def test_stream_friendly_format(self):
        """Test that JSONL format is suitable for streaming processing."""
        issues = [
            {"key": f"PROJ-{i}", "fields": {"summary": f"Issue {i}"}}
            for i in range(100)
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")

        # Should have exactly 100 lines
        assert len(lines) == 100

        # Each line should be independently parseable
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["key"] == f"PROJ-{i}"
            assert parsed["fields"]["summary"] == f"Issue {i}"

    def test_no_trailing_newline(self):
        """Test that JSONL output does not have a trailing newline."""
        issues = [
            {"key": "PROJ-1", "fields": {"summary": "Issue 1"}},
            {"key": "PROJ-2", "fields": {"summary": "Issue 2"}},
        ]

        result = format_as_jsonl(issues)

        # Should not end with newline
        assert not result.endswith("\n")

        # Should have exactly one newline (between the two issues)
        assert result.count("\n") == 1

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
        result = format_as_jsonl(issues)
        lines = result.split("\n")

        assert len(lines) == 1000

        # Verify first and last
        parsed_first = json.loads(lines[0])
        parsed_last = json.loads(lines[999])
        assert parsed_first["key"] == "PROJ-0"
        assert parsed_last["key"] == "PROJ-999"

    def test_bytes_serialization(self):
        """Test serialization of bytes objects."""
        issues = [
            {
                "key": "PROJ-123",
                "fields": {
                    "binaryData": b"Hello World",
                    "unicodeBytes": "Hello 世界".encode(),
                },
            }
        ]

        result = format_as_jsonl(issues)
        lines = result.split("\n")
        parsed = json.loads(lines[0])

        # Bytes should be decoded or converted to string
        assert isinstance(parsed["fields"]["binaryData"], str)
        assert (
            "Hello World" in parsed["fields"]["binaryData"]
            or parsed["fields"]["binaryData"] == "b'Hello World'"
        )
