"""Tests for display formatting functions."""


from temet_jira.document.display.formatters import (
    format_date,
    format_date_relative,
    get_priority,
    get_user_display,
    truncate_summary,
)


class TestFormatDate:
    """Tests for format_date function."""

    def test_none_returns_unknown(self) -> None:
        """None input returns 'Unknown'."""
        assert format_date(None) == "Unknown"

    def test_iso_format_with_timezone(self) -> None:
        """ISO format with Z timezone is parsed correctly."""
        result = format_date("2024-01-15T14:30:00Z")
        assert "2024-01-15" in result
        assert "14:30" in result

    def test_iso_format_with_offset(self) -> None:
        """ISO format with offset is parsed correctly."""
        result = format_date("2024-01-15T14:30:00+00:00")
        assert "2024-01-15" in result
        assert "14:30" in result

    def test_invalid_format_returns_input(self) -> None:
        """Invalid format returns original string."""
        assert format_date("not-a-date") == "not-a-date"


class TestFormatDateRelative:
    """Tests for format_date_relative function."""

    def test_none_returns_unknown(self) -> None:
        """None input returns 'Unknown'."""
        assert format_date_relative(None) == "Unknown"

    def test_invalid_format_returns_truncated(self) -> None:
        """Invalid but long enough strings return first 10 chars."""
        result = format_date_relative("invalid-date-string")
        assert result == "invalid-da"

    def test_short_invalid_returns_as_is(self) -> None:
        """Short invalid strings return as-is."""
        assert format_date_relative("bad") == "bad"


class TestGetPriority:
    """Tests for get_priority function."""

    def test_with_priority(self) -> None:
        """Priority name is extracted correctly."""
        fields = {"priority": {"name": "High"}}
        assert get_priority(fields) == "High"

    def test_without_priority(self) -> None:
        """Missing priority returns 'Not set'."""
        fields = {}
        assert get_priority(fields) == "Not set"

    def test_priority_none(self) -> None:
        """None priority returns 'Not set'."""
        fields = {"priority": None}
        assert get_priority(fields) == "Not set"

    def test_priority_name_none(self) -> None:
        """Priority with None name returns 'Not set'."""
        fields = {"priority": {"name": None}}
        assert get_priority(fields) == "Not set"

    def test_priority_empty_dict(self) -> None:
        """Empty priority dict returns 'Not set'."""
        fields = {"priority": {}}
        assert get_priority(fields) == "Not set"


class TestGetUserDisplay:
    """Tests for get_user_display function."""

    def test_with_display_name(self) -> None:
        """Display name is returned."""
        user = {"displayName": "John Doe", "emailAddress": "john@example.com"}
        assert get_user_display(user) == "John Doe"

    def test_with_email_fallback(self) -> None:
        """Email is used when displayName missing."""
        user = {"emailAddress": "john@example.com"}
        assert get_user_display(user) == "john@example.com"

    def test_none_user(self) -> None:
        """None user returns 'Unassigned'."""
        assert get_user_display(None) == "Unassigned"

    def test_empty_dict(self) -> None:
        """Empty dict returns 'Unassigned'."""
        assert get_user_display({}) == "Unassigned"

    def test_non_dict(self) -> None:
        """Non-dict values return 'Unknown'."""
        assert get_user_display("not a dict") == "Unknown"  # type: ignore

    def test_display_name_none(self) -> None:
        """None displayName with None email returns 'Unknown'."""
        user = {"displayName": None, "emailAddress": None}
        assert get_user_display(user) == "Unknown"


class TestTruncateSummary:
    """Tests for truncate_summary function."""

    def test_short_summary(self) -> None:
        """Short summaries are not truncated."""
        assert truncate_summary("Short text", 50) == "Short text"

    def test_exact_length(self) -> None:
        """Exact length summaries are not truncated."""
        text = "x" * 50
        assert truncate_summary(text, 50) == text

    def test_long_summary(self) -> None:
        """Long summaries are truncated with ellipsis."""
        text = "x" * 100
        result = truncate_summary(text, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_custom_length(self) -> None:
        """Custom max length is respected."""
        text = "Hello world and more text"
        result = truncate_summary(text, 10)
        assert len(result) == 10
        assert result == "Hello w..."

    def test_empty_summary(self) -> None:
        """Empty summary returns empty string."""
        assert truncate_summary("", 50) == ""

    def test_default_length(self) -> None:
        """Default length of 50 is used."""
        text = "x" * 60
        result = truncate_summary(text)
        assert len(result) == 50
