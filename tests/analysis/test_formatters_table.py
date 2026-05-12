"""Tests for table formatting functionality."""

import pytest

from temet_jira.analysis.formatters import (
    format_as_table,
    format_duration,
)


class TestFormatDuration:
    """Test suite for format_duration function."""

    def test_format_duration_zero_hours(self):
        """Test formatting zero hours."""
        result = format_duration(0)
        assert result == "0m"

    def test_format_duration_minutes_only(self):
        """Test formatting less than an hour."""
        result = format_duration(0.25)  # 15 minutes
        assert result == "15m"

        result = format_duration(0.5)  # 30 minutes
        assert result == "30m"

        result = format_duration(0.75)  # 45 minutes
        assert result == "45m"

    def test_format_duration_hours_only(self):
        """Test formatting exact hours."""
        result = format_duration(1.0)
        assert result == "1h"

        result = format_duration(5.0)
        assert result == "5h"

        result = format_duration(23.0)
        assert result == "23h"

    def test_format_duration_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        result = format_duration(1.5)  # 1 hour 30 minutes
        assert result == "1h 30m"

        result = format_duration(2.25)  # 2 hours 15 minutes
        assert result == "2h 15m"

        result = format_duration(5.75)  # 5 hours 45 minutes
        assert result == "5h 45m"

    def test_format_duration_days_only(self):
        """Test formatting exact days."""
        result = format_duration(24.0)  # 1 day
        assert result == "1d"

        result = format_duration(48.0)  # 2 days
        assert result == "2d"

        result = format_duration(72.0)  # 3 days
        assert result == "3d"

    def test_format_duration_days_and_hours(self):
        """Test formatting days and hours."""
        result = format_duration(25.0)  # 1 day 1 hour
        assert result == "1d 1h"

        result = format_duration(30.0)  # 1 day 6 hours
        assert result == "1d 6h"

        result = format_duration(50.0)  # 2 days 2 hours
        assert result == "2d 2h"

    def test_format_duration_full_format(self):
        """Test formatting with days, hours, and minutes."""
        result = format_duration(25.5)  # 1 day 1 hour 30 minutes
        assert result == "1d 1h 30m"

        result = format_duration(50.25)  # 2 days 2 hours 15 minutes
        assert result == "2d 2h 15m"

        result = format_duration(73.75)  # 3 days 1 hour 45 minutes
        assert result == "3d 1h 45m"

    def test_format_duration_large_values(self):
        """Test formatting large hour values."""
        result = format_duration(168.0)  # 1 week
        assert result == "7d"

        result = format_duration(336.5)  # 2 weeks and 30 minutes
        assert result == "14d 30m"

        result = format_duration(720.0)  # 30 days
        assert result == "30d"

    def test_format_duration_decimal_precision(self):
        """Test that decimal precision is handled correctly."""
        result = format_duration(1.999)  # Should round minutes
        assert result == "1h 59m"

        result = format_duration(0.001)  # Very small value
        assert result == "0m"  # Too small to show

        result = format_duration(0.016667)  # Exactly 1 minute
        assert result == "1m"

    def test_format_duration_negative_values(self):
        """Test that negative values are handled (though they shouldn't occur)."""
        # Negative values don't make sense for duration but should handle gracefully
        result = format_duration(-1.0)
        # Implementation might handle this differently
        # For now, test that it doesn't crash
        assert isinstance(result, str)


class TestFormatAsTable:
    """Test suite for format_as_table function."""

    def test_format_table_not_implemented(self):
        """Test that format_as_table raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Table formatting implementation pending"
        ):
            format_as_table([])

    def test_format_table_with_data_not_implemented(self):
        """Test that format_as_table raises NotImplementedError with data."""
        analysis_results = [
            {"issue_key": "TEST-100", "summary": "Test Issue", "durations": []}
        ]

        with pytest.raises(
            NotImplementedError, match="Table formatting implementation pending"
        ):
            format_as_table(analysis_results)

    def test_format_table_with_max_width_not_implemented(self):
        """Test that format_as_table raises NotImplementedError with max_width."""
        with pytest.raises(
            NotImplementedError, match="Table formatting implementation pending"
        ):
            format_as_table([], max_width=80)

    # These tests are placeholders for when the table formatter is implemented
    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_empty_results(self):
        """Test table formatting with empty results."""
        result = format_as_table([])
        assert result == ""

    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_single_issue(self):
        """Test table formatting with a single issue."""
        from datetime import UTC, datetime

        from temet_jira.analysis.state_analyzer import StateDuration

        analysis_results = [
            {
                "issue_key": "TEST-100",
                "summary": "Test Issue",
                "durations": [
                    StateDuration(
                        state="To Do",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        calendar_days=1.041667,
                        business_hours=8.0,
                    )
                ],
            }
        ]

        result = format_as_table(analysis_results)

        # Check that key elements are present
        assert "TEST-100" in result
        assert "Test Issue" in result
        assert "To Do" in result
        assert "1d" in result or "1.04" in result

    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_multiple_issues(self):
        """Test table formatting with multiple issues."""
        from datetime import UTC, datetime

        from temet_jira.analysis.state_analyzer import StateDuration

        analysis_results = [
            {
                "issue_key": "TEST-100",
                "summary": "First Issue",
                "durations": [
                    StateDuration(
                        state="To Do",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        calendar_days=1.041667,
                        business_hours=8.0,
                    )
                ],
            },
            {
                "issue_key": "TEST-101",
                "summary": "Second Issue",
                "durations": [
                    StateDuration(
                        state="In Progress",
                        start_time=datetime(2024, 1, 3, 9, 0, 0, tzinfo=UTC),
                        end_time=None,
                        calendar_days=5.0,
                        business_hours=32.0,
                    )
                ],
            },
        ]

        result = format_as_table(analysis_results)

        # Check that both issues are present
        assert "TEST-100" in result
        assert "TEST-101" in result
        assert "First Issue" in result
        assert "Second Issue" in result

    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_with_max_width(self):
        """Test table formatting with maximum width constraint."""
        from datetime import UTC, datetime

        from temet_jira.analysis.state_analyzer import StateDuration

        analysis_results = [
            {
                "issue_key": "TEST-100",
                "summary": "This is a very long summary that should be truncated when max width is applied",
                "durations": [
                    StateDuration(
                        state="To Do",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        calendar_days=1.041667,
                        business_hours=8.0,
                    )
                ],
            }
        ]

        result = format_as_table(analysis_results, max_width=50)

        # Check that lines don't exceed max width
        lines = result.split("\n")
        for line in lines:
            assert len(line) <= 50

    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_with_errors(self):
        """Test table formatting with error entries."""
        analysis_results = [
            {"issue_key": "TEST-100", "error": "Failed to process issue"},
            {"issue_key": "TEST-101", "summary": "Valid Issue", "durations": []},
        ]

        result = format_as_table(analysis_results)

        # Error issue should be shown appropriately
        assert "TEST-100" in result
        assert "Failed to process" in result or "Error" in result

        # Valid issue should still be shown
        assert "TEST-101" in result
        assert "Valid Issue" in result

    @pytest.mark.skip(reason="Table formatter not yet implemented")
    def test_format_table_alignment(self):
        """Test that table columns are properly aligned."""
        from datetime import UTC, datetime

        from temet_jira.analysis.state_analyzer import StateDuration

        analysis_results = [
            {
                "issue_key": "TEST-1",
                "summary": "Short",
                "durations": [
                    StateDuration(
                        state="To Do",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        calendar_days=1.0,
                        business_hours=8.0,
                    )
                ],
            },
            {
                "issue_key": "TEST-1000",
                "summary": "Much longer summary text",
                "durations": [
                    StateDuration(
                        state="In Progress",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 10, 17, 0, 0, tzinfo=UTC),
                        calendar_days=9.333,
                        business_hours=72.0,
                    )
                ],
            },
        ]

        result = format_as_table(analysis_results)
        lines = result.split("\n")

        # Check that columns align (e.g., all "TEST-" prefixes start at same position)
        test_positions = [line.find("TEST-") for line in lines if "TEST-" in line]
        if test_positions:
            # All TEST- should start at the same position
            assert len(set(test_positions)) == 1
