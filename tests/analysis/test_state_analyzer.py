"""Tests for StateDurationAnalyzer class."""

from datetime import UTC, datetime

import pytest

from temet_jira.analysis.state_analyzer import (
    StateDurationAnalyzer,
    StateTransition,
)


class TestStateTransition:
    """Tests for StateTransition dataclass."""

    def test_state_transition_creation(self):
        """Test creating a StateTransition instance."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        transition = StateTransition(
            timestamp=timestamp,
            from_state="To Do",
            to_state="In Progress",
            author="john.doe",
        )

        assert transition.timestamp == timestamp
        assert transition.from_state == "To Do"
        assert transition.to_state == "In Progress"
        assert transition.author == "john.doe"

    def test_state_transition_optional_author(self):
        """Test StateTransition with optional author field."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        transition = StateTransition(
            timestamp=timestamp, from_state="To Do", to_state="In Progress"
        )

        assert transition.author is None


class TestExtractStateTransitions:
    """Tests for extract_state_transitions method."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_extract_transitions_with_complete_changelog(self, analyzer):
        """Test extracting transitions from issue with complete changelog."""
        issue = {
            "key": "TEST-123",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0000",
                        "author": {"accountId": "user123", "displayName": "John Doe"},
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "from": "1",
                                "fromString": "To Do",
                                "to": "2",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-03T14:00:00.000+0000",
                        "author": {"accountId": "user456", "displayName": "Jane Smith"},
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "from": "2",
                                "fromString": "In Progress",
                                "to": "3",
                                "toString": "Done",
                            }
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 3

        # Check initial state (created -> first transition)
        assert transitions[0].from_state is None
        assert transitions[0].to_state == "To Do"
        assert transitions[0].timestamp == datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC)

        # Check first transition
        assert transitions[1].from_state == "To Do"
        assert transitions[1].to_state == "In Progress"
        assert transitions[1].timestamp == datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC)
        assert transitions[1].author == "John Doe"

        # Check second transition
        assert transitions[2].from_state == "In Progress"
        assert transitions[2].to_state == "Done"
        assert transitions[2].timestamp == datetime(2024, 1, 3, 14, 0, 0, tzinfo=UTC)
        assert transitions[2].author == "Jane Smith"

    def test_extract_transitions_no_changelog(self, analyzer):
        """Test extracting transitions from issue without changelog."""
        issue = {
            "key": "TEST-124",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "To Do"},
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 1
        assert transitions[0].from_state is None
        assert transitions[0].to_state == "To Do"
        assert transitions[0].timestamp == datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC)
        assert transitions[0].author is None

    def test_extract_transitions_empty_changelog(self, analyzer):
        """Test extracting transitions from issue with empty changelog."""
        issue = {
            "key": "TEST-125",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "In Progress"},
            },
            "changelog": {"histories": []},
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 1
        assert transitions[0].from_state is None
        assert transitions[0].to_state == "In Progress"
        assert transitions[0].timestamp == datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC)

    def test_extract_transitions_no_status_changes(self, analyzer):
        """Test extracting transitions when changelog has no status changes."""
        issue = {
            "key": "TEST-126",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "To Do"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0000",
                        "items": [
                            {
                                "field": "priority",
                                "fromString": "Low",
                                "toString": "High",
                            }
                        ],
                    }
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 1
        assert transitions[0].to_state == "To Do"

    def test_extract_transitions_mixed_changes(self, analyzer):
        """Test extracting only status transitions from mixed changelog."""
        issue = {
            "key": "TEST-127",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0000",
                        "items": [
                            {
                                "field": "priority",
                                "fromString": "Low",
                                "toString": "Medium",
                            },
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            },
                        ],
                    }
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 2
        assert transitions[1].from_state == "To Do"
        assert transitions[1].to_state == "In Progress"

    def test_extract_transitions_chronological_order(self, analyzer):
        """Test that transitions are returned in chronological order."""
        issue = {
            "key": "TEST-128",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-03T14:00:00.000+0000",  # Later date
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Done",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-02T10:00:00.000+0000",  # Earlier date
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 3
        # Verify chronological order
        assert transitions[0].timestamp < transitions[1].timestamp
        assert transitions[1].timestamp < transitions[2].timestamp
        assert transitions[1].to_state == "In Progress"
        assert transitions[2].to_state == "Done"

    def test_extract_transitions_invalid_timestamp(self, analyzer):
        """Test handling of invalid timestamp formats."""
        issue = {
            "key": "TEST-129",
            "fields": {"created": "invalid-timestamp", "status": {"name": "To Do"}},
        }

        with pytest.raises(ValueError, match="Invalid timestamp format"):
            analyzer.extract_state_transitions(issue)

    def test_extract_transitions_missing_status_field(self, analyzer):
        """Test handling when status field is missing."""
        issue = {
            "key": "TEST-130",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000"
                # Missing status field
            },
        }

        with pytest.raises(KeyError, match="status"):
            analyzer.extract_state_transitions(issue)

    def test_extract_transitions_missing_author(self, analyzer):
        """Test handling when author information is missing."""
        issue = {
            "key": "TEST-131",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0000",
                        # Missing author
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    }
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 2
        assert transitions[1].author is None

    def test_extract_transitions_with_timezone(self, analyzer):
        """Test correct parsing of timestamps with different timezones."""
        issue = {
            "key": "TEST-132",
            "fields": {
                "created": "2024-01-01T09:00:00.000-0500",  # EST
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-02T10:00:00.000+0100",  # CET
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    }
                ]
            },
        }

        transitions = analyzer.extract_state_transitions(issue)

        assert len(transitions) == 2
        # Timestamps should be parsed correctly with timezone info
        assert transitions[0].timestamp.tzinfo is not None
        assert transitions[1].timestamp.tzinfo is not None


class TestCalculateDurations:
    """Tests for calculate_durations method."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_calculate_durations_empty_transitions(self, analyzer):
        """Test calculation with empty transitions list."""
        durations = analyzer.calculate_durations([])
        assert durations == []

    def test_calculate_durations_single_transition(self, analyzer):
        """Test duration calculation with single transition (still active)."""
        transition = StateTransition(
            timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
            from_state=None,
            to_state="To Do",
        )

        durations = analyzer.calculate_durations([transition])

        assert len(durations) == 1
        assert durations[0].state == "To Do"
        assert durations[0].start_time == transition.timestamp
        assert durations[0].end_time is None  # Still active
        assert durations[0].calendar_days > 0  # Should be positive time
        assert durations[0].business_hours >= 0

    def test_calculate_durations_multiple_transitions(self, analyzer):
        """Test duration calculation with multiple transitions."""
        transitions = [
            StateTransition(
                timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                from_state=None,
                to_state="To Do",
            ),
            StateTransition(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                from_state="To Do",
                to_state="In Progress",
            ),
            StateTransition(
                timestamp=datetime(2024, 1, 5, 14, 0, 0, tzinfo=UTC),
                from_state="In Progress",
                to_state="Done",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 3

        # First state duration
        assert durations[0].state == "To Do"
        assert durations[0].start_time == transitions[0].timestamp
        assert durations[0].end_time == transitions[1].timestamp
        assert durations[0].calendar_days == pytest.approx(
            1.041667, rel=0.01
        )  # ~25 hours

        # Second state duration
        assert durations[1].state == "In Progress"
        assert durations[1].start_time == transitions[1].timestamp
        assert durations[1].end_time == transitions[2].timestamp
        assert durations[1].calendar_days == pytest.approx(
            3.166667, rel=0.01
        )  # ~76 hours

        # Third state (current)
        assert durations[2].state == "Done"
        assert durations[2].start_time == transitions[2].timestamp
        assert durations[2].end_time is None

    def test_calculate_durations_timezone_handling(self, analyzer):
        """Test that mixed timezones are handled correctly."""
        transitions = [
            StateTransition(
                timestamp=datetime(2024, 1, 1, 9, 0, 0),  # Naive datetime
                from_state=None,
                to_state="To Do",
            ),
            StateTransition(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),  # Aware datetime
                from_state="To Do",
                to_state="In Progress",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2
        # Should handle naive datetime by converting to UTC
        assert durations[0].calendar_days == pytest.approx(1.041667, rel=0.01)


class TestBusinessHoursCalculation:
    """Tests for business hours calculation."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_business_hours_same_day(self, analyzer):
        """Test business hours calculation within same day."""
        start = datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC)  # Tuesday 10 AM
        end = datetime(2024, 1, 2, 15, 0, 0, tzinfo=UTC)  # Tuesday 3 PM

        hours = analyzer._calculate_business_hours(start, end)
        assert hours == 5.0

    def test_business_hours_across_days(self, analyzer):
        """Test business hours calculation across multiple days."""
        start = datetime(2024, 1, 2, 15, 0, 0, tzinfo=UTC)  # Tuesday 3 PM
        end = datetime(2024, 1, 4, 11, 0, 0, tzinfo=UTC)  # Thursday 11 AM

        hours = analyzer._calculate_business_hours(start, end)
        # Tuesday: 2 hours (3 PM - 5 PM)
        # Wednesday: 8 hours (9 AM - 5 PM)
        # Thursday: 2 hours (9 AM - 11 AM)
        assert hours == 12.0

    def test_business_hours_weekend_excluded(self, analyzer):
        """Test that weekends are excluded from business hours."""
        start = datetime(2024, 1, 5, 15, 0, 0, tzinfo=UTC)  # Friday 3 PM
        end = datetime(2024, 1, 8, 11, 0, 0, tzinfo=UTC)  # Monday 11 AM

        hours = analyzer._calculate_business_hours(start, end)
        # Friday: 2 hours (3 PM - 5 PM)
        # Saturday & Sunday: 0 hours
        # Monday: 2 hours (9 AM - 11 AM)
        assert hours == 4.0

    def test_business_hours_outside_business_hours(self, analyzer):
        """Test calculation when times are outside business hours."""
        start = datetime(2024, 1, 2, 6, 0, 0, tzinfo=UTC)  # Tuesday 6 AM (before 9 AM)
        end = datetime(2024, 1, 2, 20, 0, 0, tzinfo=UTC)  # Tuesday 8 PM (after 5 PM)

        hours = analyzer._calculate_business_hours(start, end)
        # Should only count 9 AM - 5 PM
        assert hours == 8.0

    def test_business_hours_start_after_end(self, analyzer):
        """Test that reversed times return 0."""
        start = datetime(2024, 1, 2, 15, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC)

        hours = analyzer._calculate_business_hours(start, end)
        assert hours == 0.0

    def test_business_hours_custom_hours(self, analyzer):
        """Test custom business hours configuration."""
        analyzer.business_hours_start = 8  # 8 AM
        analyzer.business_hours_end = 18  # 6 PM

        start = datetime(2024, 1, 2, 8, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 2, 18, 0, 0, tzinfo=UTC)

        hours = analyzer._calculate_business_hours(start, end)
        assert hours == 10.0  # 8 AM - 6 PM = 10 hours


class TestAnalyzeIssues:
    """Tests for analyze_issues method."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_analyze_issues_empty_list(self, analyzer):
        """Test analyzing empty issues list."""
        results = analyzer.analyze_issues([])
        assert results == []

    def test_analyze_issues_single_issue(self, analyzer):
        """Test analyzing a single issue."""
        issue = {
            "key": "TEST-100",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "summary": "Test Issue",
                "status": {"name": "To Do"},
            },
        }

        results = analyzer.analyze_issues([issue])

        assert len(results) == 1
        assert results[0]["issue_key"] == "TEST-100"
        assert results[0]["summary"] == "Test Issue"
        assert "transitions" in results[0]
        assert "durations" in results[0]

    def test_analyze_issues_with_date_filters(self, analyzer):
        """Test analyzing issues with date range filters."""
        issue = {
            "key": "TEST-101",
            "fields": {
                "created": "2024-01-01T09:00:00.000+0000",
                "status": {"name": "Done"},
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2024-01-05T10:00:00.000+0000",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2024-01-10T14:00:00.000+0000",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Done",
                            }
                        ],
                    },
                ]
            },
        }

        # Filter to only include transitions after Jan 5
        from_date = datetime(2024, 1, 6, 0, 0, 0, tzinfo=UTC)
        results = analyzer.analyze_issues([issue], from_date=from_date)

        assert len(results) == 1
        # Should only have the second transition (Jan 10)
        transitions = results[0]["transitions"]
        assert len(transitions) == 1
        assert transitions[0].to_state == "Done"

    def test_analyze_issues_with_error_handling(self, analyzer):
        """Test that errors in one issue don't stop processing others."""
        issues = [
            {
                "key": "TEST-102",
                "fields": {
                    # Missing required fields - will cause error
                },
            },
            {
                "key": "TEST-103",
                "fields": {
                    "created": "2024-01-01T09:00:00.000+0000",
                    "summary": "Valid Issue",
                    "status": {"name": "To Do"},
                },
            },
        ]

        results = analyzer.analyze_issues(issues)

        assert len(results) == 2
        # First issue should have error
        assert "error" in results[0]
        assert results[0]["issue_key"] == "TEST-102"

        # Second issue should be processed normally
        assert "error" not in results[1]
        assert results[1]["issue_key"] == "TEST-103"
        assert results[1]["summary"] == "Valid Issue"


class TestFormatAsCSV:
    """Tests for CSV formatting of state analysis results."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_format_csv_empty_results(self, analyzer):
        """Test CSV formatting with empty results."""
        csv_output = analyzer.format_as_csv([])

        # Should still have headers
        assert "Issue Key" in csv_output
        assert "State" in csv_output
        assert "Calendar Days" in csv_output

    def test_format_csv_with_results(self, analyzer):
        """Test CSV formatting with analysis results."""
        from temet_jira.analysis.state_analyzer import StateDuration

        results = [
            {
                "issue_key": "TEST-200",
                "durations": [
                    StateDuration(
                        state="To Do",
                        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                        end_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        calendar_days=1.041667,
                        business_hours=8.0,
                    ),
                    StateDuration(
                        state="In Progress",
                        start_time=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
                        end_time=None,
                        calendar_days=5.0,
                        business_hours=32.0,
                    ),
                ],
            }
        ]

        csv_output = analyzer.format_as_csv(results)

        lines = csv_output.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows

        # Check header
        assert "Issue Key" in lines[0]
        assert "State" in lines[0]

        # Check data
        assert "TEST-200" in lines[1]
        assert "To Do" in lines[1]
        assert "1.04" in lines[1]  # Calendar days

        assert "TEST-200" in lines[2]
        assert "In Progress" in lines[2]
        assert "Current" in lines[2]  # End time for active state

    def test_format_csv_with_business_hours(self, analyzer):
        """Test CSV formatting with business hours included."""
        from temet_jira.analysis.state_analyzer import StateDuration

        results = [
            {
                "issue_key": "TEST-201",
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

        csv_output = analyzer.format_as_csv(results, include_business_hours=True)

        lines = csv_output.strip().split("\n")
        header = lines[0]

        assert "Business Hours" in header
        assert "8.00" in lines[1]  # Business hours value

    def test_format_csv_skip_errored_issues(self, analyzer):
        """Test that CSV formatting skips issues with errors."""
        results = [
            {"issue_key": "TEST-202", "error": "Failed to process"},
            {"issue_key": "TEST-203", "durations": []},
        ]

        csv_output = analyzer.format_as_csv(results)

        lines = csv_output.strip().split("\n")
        # Should only have header (errored issue skipped, empty durations produce no rows)
        assert len(lines) == 1
        assert "TEST-202" not in csv_output
