"""Test that the analysis module structure is correctly set up."""

import pytest


def test_analysis_module_imports():
    """Test that all analysis module components can be imported."""
    # Test direct imports from analysis module
    from temet_jira.analysis import (
        StateDurationAnalyzer,
        format_as_csv,
        format_as_json,
    )

    assert StateDurationAnalyzer is not None
    assert format_as_json is not None
    assert format_as_csv is not None


def test_parent_module_imports():
    """Test that analysis components are accessible from parent jira module."""
    from temet_jira import (
        StateDurationAnalyzer,
        format_as_csv,
        format_as_json,
    )

    assert StateDurationAnalyzer is not None
    assert format_as_json is not None
    assert format_as_csv is not None


def test_state_analyzer_initialization():
    """Test that StateDurationAnalyzer can be instantiated."""
    from temet_jira.analysis import StateDurationAnalyzer

    analyzer = StateDurationAnalyzer()
    assert analyzer is not None
    assert analyzer.jira_client is None

    # Test with mock client
    mock_client = object()
    analyzer_with_client = StateDurationAnalyzer(jira_client=mock_client)
    assert analyzer_with_client.jira_client is mock_client


def test_formatters_basic_functionality():
    """Test basic functionality of formatter functions."""
    import json

    from temet_jira.analysis import format_as_csv, format_as_json

    # Test with empty data
    empty_json = format_as_json([])
    # Should return a valid JSON array
    assert empty_json == "[]"
    parsed = json.loads(empty_json)
    assert isinstance(parsed, list)
    assert len(parsed) == 0

    empty_csv = format_as_csv([])
    assert empty_csv == ""

    # Test with sample data
    sample_data = [{"issue_key": "TEST-1", "summary": "Test Issue"}]

    json_output = format_as_json(sample_data)
    assert "TEST-1" in json_output
    assert "Test Issue" in json_output

    csv_output = format_as_csv(sample_data)
    # CSV should have header when include_header=True (default)
    assert "issue_key" in csv_output


def test_format_duration_helper():
    """Test the format_duration helper function."""
    from temet_jira.analysis.formatters import format_duration

    # Test various duration formats
    assert format_duration(0) == "0m"
    assert format_duration(0.5) == "30m"
    assert format_duration(1.5) == "1h 30m"
    assert format_duration(25.5) == "1d 1h 30m"
    assert format_duration(48) == "2d"


def test_not_implemented_methods():
    """Test that placeholder methods raise NotImplementedError."""
    from temet_jira.analysis import StateDurationAnalyzer

    analyzer = StateDurationAnalyzer()

    # analyze_issue and analyze_issues are now implemented, so we don't test for NotImplementedError
    # calculate_durations is now implemented (TASK-010), so we don't test for NotImplementedError

    with pytest.raises(
        NotImplementedError, match="Summary generation implementation pending"
    ):
        analyzer.get_state_summary()
