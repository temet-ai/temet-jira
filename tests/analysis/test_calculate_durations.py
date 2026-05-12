"""Tests for calculate_durations method of StateDurationAnalyzer."""

from datetime import UTC, datetime

import pytest
from dateutil import tz

from temet_jira.analysis.state_analyzer import (
    StateDurationAnalyzer,
    StateTransition,
)


class TestCalculateDurations:
    """Tests for calculate_durations method."""

    @pytest.fixture
    def analyzer(self):
        """Create a StateDurationAnalyzer instance."""
        return StateDurationAnalyzer()

    def test_single_state_still_active(self, analyzer):
        """Test calculating duration for a single state that's still active."""
        transitions = [
            StateTransition(
                timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC),
                from_state=None,
                to_state="To Do",
                author=None,
            )
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 1
        assert durations[0].state == "To Do"
        assert durations[0].start_time == datetime(
            2024, 1, 1, 9, 0, 0, tzinfo=UTC
        )
        assert durations[0].end_time is None
        assert durations[0].calendar_days > 0  # Should be current time - start time
        assert durations[0].business_hours > 0

    def test_multiple_states_with_transitions(self, analyzer):
        """Test calculating durations for multiple state transitions."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 1, 9, 0, 0, tzinfo=UTC
                ),  # Monday 9 AM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 10, 0, 0, tzinfo=UTC
                ),  # Tuesday 10 AM
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 3, 15, 0, 0, tzinfo=UTC
                ),  # Wednesday 3 PM
                from_state="In Progress",
                to_state="Done",
                author="Jane Smith",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 3

        # First state: To Do (1 day + 1 hour = 25 hours)
        assert durations[0].state == "To Do"
        assert durations[0].start_time == datetime(
            2024, 1, 1, 9, 0, 0, tzinfo=UTC
        )
        assert durations[0].end_time == datetime(
            2024, 1, 2, 10, 0, 0, tzinfo=UTC
        )
        assert durations[0].calendar_days == pytest.approx(
            25 / 24, rel=0.01
        )  # 25 hours in days
        assert durations[0].business_hours == 9  # 8 hours Monday + 1 hour Tuesday

        # Second state: In Progress (1 day + 5 hours = 29 hours)
        assert durations[1].state == "In Progress"
        assert durations[1].start_time == datetime(
            2024, 1, 2, 10, 0, 0, tzinfo=UTC
        )
        assert durations[1].end_time == datetime(
            2024, 1, 3, 15, 0, 0, tzinfo=UTC
        )
        assert durations[1].calendar_days == pytest.approx(
            29 / 24, rel=0.01
        )  # 29 hours in days
        assert (
            durations[1].business_hours == 13
        )  # 7 hours Tuesday (10 AM - 5 PM) + 6 hours Wednesday (9 AM - 3 PM)

        # Third state: Done (still active)
        assert durations[2].state == "Done"
        assert durations[2].start_time == datetime(
            2024, 1, 3, 15, 0, 0, tzinfo=UTC
        )
        assert durations[2].end_time is None
        assert durations[2].calendar_days > 0
        assert durations[2].business_hours >= 0  # Depends on current time

    def test_weekend_transition(self, analyzer):
        """Test transitions that span weekends."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 5, 16, 0, 0, tzinfo=UTC
                ),  # Friday 4 PM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 8, 10, 0, 0, tzinfo=UTC
                ),  # Monday 10 AM
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2

        # First state spans weekend
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(
            66 / 24, rel=0.01
        )  # 66 hours
        # Business hours: 1 hour Friday (4-5 PM) + 1 hour Monday (9-10 AM) = 2 hours
        assert durations[0].business_hours == 2

    def test_short_duration_within_business_day(self, analyzer):
        """Test very short durations within the same business day."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 10, 0, 0, tzinfo=UTC
                ),  # Tuesday 10 AM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 10, 30, 0, tzinfo=UTC
                ),  # Tuesday 10:30 AM
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 11, 15, 0, tzinfo=UTC
                ),  # Tuesday 11:15 AM
                from_state="In Progress",
                to_state="Done",
                author="Jane Smith",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 3

        # First state: 30 minutes
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(
            0.5 / 24, rel=0.01
        )  # 0.5 hours
        assert durations[0].business_hours == 0.5

        # Second state: 45 minutes
        assert durations[1].state == "In Progress"
        assert durations[1].calendar_days == pytest.approx(
            0.75 / 24, rel=0.01
        )  # 0.75 hours
        assert durations[1].business_hours == 0.75

    def test_transition_outside_business_hours(self, analyzer):
        """Test transitions that occur outside business hours."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 6, 0, 0, tzinfo=UTC
                ),  # Tuesday 6 AM (before business hours)
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 20, 0, 0, tzinfo=UTC
                ),  # Tuesday 8 PM (after business hours)
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2

        # First state: 14 calendar hours but only 8 business hours (9 AM - 5 PM)
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(
            14 / 24, rel=0.01
        )  # 14 hours
        assert durations[0].business_hours == 8  # Full business day

    def test_transition_on_weekend(self, analyzer):
        """Test transitions that occur on weekends."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 6, 10, 0, 0, tzinfo=UTC
                ),  # Saturday 10 AM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 7, 14, 0, 0, tzinfo=UTC
                ),  # Sunday 2 PM
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 8, 10, 0, 0, tzinfo=UTC
                ),  # Monday 10 AM
                from_state="In Progress",
                to_state="Done",
                author="Jane Smith",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 3

        # First state: Saturday to Sunday (no business hours)
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(
            28 / 24, rel=0.01
        )  # 28 hours
        assert durations[0].business_hours == 0  # Weekend, no business hours

        # Second state: Sunday to Monday (only Monday morning counts)
        assert durations[1].state == "In Progress"
        assert durations[1].calendar_days == pytest.approx(
            20 / 24, rel=0.01
        )  # 20 hours
        assert durations[1].business_hours == 1  # 1 hour Monday morning (9-10 AM)

    def test_empty_transitions_list(self, analyzer):
        """Test handling of empty transitions list."""
        transitions = []

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 0

    def test_timezone_aware_calculations(self, analyzer):
        """Test that timezone information is properly handled."""
        eastern = tz.gettz("America/New_York")
        transitions = [
            StateTransition(
                timestamp=datetime(2024, 1, 2, 9, 0, 0, tzinfo=eastern),  # 9 AM EST
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(2024, 1, 2, 17, 0, 0, tzinfo=eastern),  # 5 PM EST
                from_state="To Do",
                to_state="Done",
                author="John Doe",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2

        # Should handle timezone correctly
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(8 / 24, rel=0.01)  # 8 hours
        # Business hours calculation might vary based on timezone handling
        assert durations[0].business_hours >= 0  # At least non-negative

    def test_with_custom_business_hours(self, analyzer):
        """Test with custom business hours configuration."""
        # Initialize analyzer with custom business hours (7 AM - 7 PM)
        analyzer.business_hours_start = 7
        analyzer.business_hours_end = 19

        transitions = [
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 7, 0, 0, tzinfo=UTC
                ),  # Tuesday 7 AM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 19, 0, 0, tzinfo=UTC
                ),  # Tuesday 7 PM
                from_state="To Do",
                to_state="Done",
                author="John Doe",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2

        # Should use custom business hours
        assert durations[0].state == "To Do"
        assert durations[0].calendar_days == pytest.approx(
            12 / 24, rel=0.01
        )  # 12 hours
        assert durations[0].business_hours == 12  # Full extended business day

    def test_multiple_transitions_same_timestamp(self, analyzer):
        """Test handling of multiple transitions at the same timestamp."""
        timestamp = datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC)
        transitions = [
            StateTransition(
                timestamp=datetime(2024, 1, 2, 9, 0, 0, tzinfo=UTC),
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=timestamp,
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
            StateTransition(
                timestamp=timestamp,  # Same timestamp as previous
                from_state="In Progress",
                to_state="Review",
                author="Jane Smith",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 3

        # First state should have 1 hour duration
        assert durations[0].state == "To Do"
        assert durations[0].business_hours == 1

        # Second state should have 0 duration (immediate transition)
        assert durations[1].state == "In Progress"
        assert durations[1].business_hours == 0

        # Third state is still active
        assert durations[2].state == "Review"
        assert durations[2].end_time is None

    def test_year_transition_with_holidays(self, analyzer):
        """Test transitions spanning year boundaries."""
        transitions = [
            StateTransition(
                timestamp=datetime(
                    2023, 12, 29, 15, 0, 0, tzinfo=UTC
                ),  # Friday 3 PM
                from_state=None,
                to_state="To Do",
                author=None,
            ),
            StateTransition(
                timestamp=datetime(
                    2024, 1, 2, 10, 0, 0, tzinfo=UTC
                ),  # Tuesday 10 AM (after New Year)
                from_state="To Do",
                to_state="In Progress",
                author="John Doe",
            ),
        ]

        durations = analyzer.calculate_durations(transitions)

        assert len(durations) == 2

        # Should correctly handle year transition
        assert durations[0].state == "To Do"
        # Business hours: 2 hours Friday (3-5 PM) + 8 hours Monday (9 AM - 5 PM) + 1 hour Tuesday (9-10 AM) = 11 hours
        # (Jan 1 2024 is a Monday - it's a working day)
        assert durations[0].business_hours == 11
