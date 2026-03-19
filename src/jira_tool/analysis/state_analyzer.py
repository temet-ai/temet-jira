"""State duration analyzer for Jira issues."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class StateTransition:
    """Represents a single state transition in an issue's lifecycle."""

    timestamp: datetime
    from_state: str | None
    to_state: str
    author: str | None = None


@dataclass
class StateDuration:
    """Represents time spent in a specific state."""

    state: str
    start_time: datetime
    end_time: datetime | None  # None if still in this state
    calendar_days: float
    business_hours: float


class StateDurationAnalyzer:
    """Analyzer for calculating state durations of Jira issues.

    This class analyzes the time spent in different states for Jira issues
    based on their changelog history.
    """

    def __init__(self, jira_client: Any | None = None):
        """Initialize the state duration analyzer.

        Args:
            jira_client: Optional Jira client instance for fetching issue data.
        """
        self.jira_client = jira_client
        self._state_durations: dict[str, list[dict[str, Any]]] = {}
        self.business_hours_start = 9  # 9 AM
        self.business_hours_end = 17  # 5 PM

    def analyze_issue(self, issue_key: str) -> dict[str, Any]:
        """Analyze state durations for a single issue.

        Args:
            issue_key: The Jira issue key to analyze.

        Returns:
            Dictionary containing state duration analysis results.
        """
        # Implementation will be added in later tasks
        raise NotImplementedError("State analysis implementation pending")

    def analyze_issues_business_hours(
        self,
        issues: list[dict[str, Any]],
        timezone: str | None = None,
    ) -> list[dict[str, Any]]:
        """Analyze state durations for multiple issues using business hours.

        Args:
            issues: List of Jira issue data with expanded changelog.
            timezone: Optional timezone string for business hours calculation.

        Returns:
            List of dictionaries containing analysis results for each issue.
        """
        # Delegate to analyze_issues — business hours are always calculated
        return self.analyze_issues(issues)

    def analyze_issues(
        self,
        issues: list[dict[str, Any]],
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Analyze state durations for multiple issues.

        Args:
            issues: List of Jira issue data with expanded changelog.
            from_date: Optional start date for filtering transitions.
            to_date: Optional end date for filtering transitions.

        Returns:
            List of dictionaries containing analysis results for each issue.
        """
        results = []

        for issue in issues:
            try:
                # Extract transitions for this issue
                transitions = self.extract_state_transitions(issue)

                # Apply date filters if provided
                if from_date or to_date:
                    filtered_transitions = []
                    for transition in transitions:
                        if from_date and transition.timestamp < from_date:
                            continue
                        if to_date and transition.timestamp > to_date:
                            continue
                        filtered_transitions.append(transition)
                    transitions = filtered_transitions

                # Calculate durations
                durations = self.calculate_durations(transitions)

                # Add to results
                results.append(
                    {
                        "issue_key": issue.get("key"),
                        "summary": issue.get("fields", {}).get("summary", ""),
                        "transitions": transitions,
                        "durations": durations,
                    }
                )
            except Exception as e:
                # Log error but continue processing other issues
                results.append(
                    {"issue_key": issue.get("key", "Unknown"), "error": str(e)}
                )

        return results

    def calculate_durations(
        self, transitions: list[StateTransition]
    ) -> list[StateDuration]:
        """Calculate duration spent in each state from transitions.

        Args:
            transitions: List of StateTransition objects in chronological order.

        Returns:
            List of StateDuration objects with time calculations.
        """
        if not transitions:
            return []

        durations = []
        current_time = datetime.now(UTC)

        for i, transition in enumerate(transitions):
            # Determine end time
            if i < len(transitions) - 1:
                # There's a next transition
                end_time = transitions[i + 1].timestamp
            else:
                # This is the last state, still active
                end_time = None

            # Calculate calendar days
            calc_end_time = end_time if end_time else current_time
            # Ensure both timestamps are timezone-aware for comparison
            if transition.timestamp.tzinfo is None:
                start_aware = transition.timestamp.replace(tzinfo=UTC)
            else:
                start_aware = transition.timestamp

            if calc_end_time.tzinfo is None:
                end_aware = calc_end_time.replace(tzinfo=UTC)
            else:
                end_aware = calc_end_time

            duration_seconds = (end_aware - start_aware).total_seconds()
            calendar_days = duration_seconds / (24 * 3600)

            # Calculate business hours
            business_hours = self._calculate_business_hours(start_aware, end_aware)

            durations.append(
                StateDuration(
                    state=transition.to_state,
                    start_time=transition.timestamp,
                    end_time=end_time,
                    calendar_days=calendar_days,
                    business_hours=business_hours,
                )
            )

        return durations

    def get_state_summary(self) -> dict[str, Any]:
        """Get summary statistics for all analyzed states.

        Returns:
            Dictionary containing summary statistics.
        """
        # Implementation will be added in later tasks
        raise NotImplementedError("Summary generation implementation pending")

    def format_as_csv(
        self,
        analysis_results: list[dict[str, Any]],
        include_business_hours: bool = False,
    ) -> str:
        """Format analysis results as CSV.

        Args:
            analysis_results: Results from analyze_issues method.
            include_business_hours: Whether to include business hours column.

        Returns:
            CSV formatted string.
        """
        import csv
        import io

        output = io.StringIO()

        # Define columns
        fieldnames = ["Issue Key", "State", "Start Time", "End Time", "Calendar Days"]
        if include_business_hours:
            fieldnames.append("Business Hours")

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in analysis_results:
            if "error" in result:
                # Skip errored issues
                continue

            issue_key = result["issue_key"]
            durations = result.get("durations", [])

            for duration in durations:
                row = {
                    "Issue Key": issue_key,
                    "State": duration.state,
                    "Start Time": duration.start_time.isoformat(),
                    "End Time": (
                        duration.end_time.isoformat()
                        if duration.end_time
                        else "Current"
                    ),
                    "Calendar Days": f"{duration.calendar_days:.2f}",
                }
                if include_business_hours:
                    row["Business Hours"] = f"{duration.business_hours:.2f}"

                writer.writerow(row)

        return output.getvalue()

    def extract_state_transitions(self, issue: dict[str, Any]) -> list[StateTransition]:
        """Extract state transitions from issue changelog.

        Args:
            issue: The Jira issue data with expanded changelog.

        Returns:
            List of StateTransition objects in chronological order.

        Raises:
            ValueError: If timestamp format is invalid.
            KeyError: If required fields are missing.
        """
        transitions = []

        # Validate required fields
        if "fields" not in issue:
            raise KeyError("'fields' not found in issue data")
        if "status" not in issue["fields"]:
            raise KeyError("'status' not found in issue fields")

        # Parse created timestamp
        try:
            created_timestamp = self._parse_timestamp(issue["fields"]["created"])
        except Exception as e:
            raise ValueError(
                f"Invalid timestamp format: {issue['fields']['created']}"
            ) from e

        # Get current status
        current_status = issue["fields"]["status"]["name"]

        # Check if changelog exists
        if "changelog" not in issue or not issue["changelog"].get("histories"):
            # No changelog - issue has been in current state since creation
            transitions.append(
                StateTransition(
                    timestamp=created_timestamp,
                    from_state=None,
                    to_state=current_status,
                    author=None,
                )
            )
            return transitions

        # Process changelog to find status transitions
        status_transitions = []
        for history in issue["changelog"]["histories"]:
            # Check each item in history for status changes
            for item in history.get("items", []):
                if item.get("field") == "status":
                    # Parse timestamp for this transition
                    try:
                        transition_timestamp = self._parse_timestamp(history["created"])
                    except Exception:
                        continue  # Skip invalid timestamps

                    # Extract author information
                    author = None
                    if "author" in history:
                        author = history["author"].get("displayName")

                    status_transitions.append(
                        {
                            "timestamp": transition_timestamp,
                            "from_state": item.get("fromString"),
                            "to_state": item.get("toString"),
                            "author": author,
                        }
                    )

        # Sort transitions by timestamp
        status_transitions.sort(key=lambda x: x["timestamp"])

        # Determine initial state
        if status_transitions:
            # Initial state is the from_state of the first transition
            initial_state = status_transitions[0]["from_state"]
        else:
            # No status transitions, use current state
            initial_state = current_status

        # Add initial state transition (creation)
        transitions.append(
            StateTransition(
                timestamp=created_timestamp,
                from_state=None,
                to_state=initial_state,
                author=None,
            )
        )

        # Add all status transitions
        for trans in status_transitions:
            transitions.append(
                StateTransition(
                    timestamp=trans["timestamp"],
                    from_state=trans["from_state"],
                    to_state=trans["to_state"],
                    author=trans["author"],
                )
            )

        return transitions

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Jira timestamp string to datetime object.

        Args:
            timestamp_str: Timestamp string in ISO format.

        Returns:
            Parsed datetime object with timezone information.
        """
        from dateutil import parser

        return parser.parse(timestamp_str)

    def _calculate_business_hours(
        self, start_time: datetime, end_time: datetime
    ) -> float:
        """Calculate business hours between two timestamps.

        Excludes weekends and only counts hours within business hours (9 AM - 5 PM).

        Args:
            start_time: Start timestamp (timezone-aware).
            end_time: End timestamp (timezone-aware).

        Returns:
            Number of business hours between the timestamps.
        """
        if start_time >= end_time:
            return 0.0

        total_hours = 0.0
        current_day = start_time.date()
        end_day = end_time.date()

        while current_day <= end_day:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_day.weekday() < 5:  # Monday=0 through Friday=4
                # Determine the business hours for this day
                day_start = datetime.combine(
                    current_day,
                    datetime.min.time().replace(hour=self.business_hours_start),
                    tzinfo=start_time.tzinfo,
                )
                day_end = datetime.combine(
                    current_day,
                    datetime.min.time().replace(hour=self.business_hours_end),
                    tzinfo=start_time.tzinfo,
                )

                # Adjust for the actual start/end times
                if current_day == start_time.date():
                    day_start = max(day_start, start_time)
                if current_day == end_time.date():
                    day_end = min(day_end, end_time)

                # Calculate hours for this day
                if day_start < day_end:
                    day_hours = (day_end - day_start).total_seconds() / 3600
                    total_hours += day_hours

            # Move to next day
            current_day += timedelta(days=1)

        return total_hours
