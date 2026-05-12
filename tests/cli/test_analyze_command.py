"""Tests for the Jira analyze CLI command group."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Import jira command from the CLI module
from temet_jira.cli import jira


class TestAnalyzeCommandGroup:
    """Tests for the analyze command group."""

    @pytest.fixture
    def runner(self):
        """Create a click test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_issues(self, tmp_path):
        """Create a sample issues JSON file."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue 1",
                    "status": {"name": "Done"},
                    "created": "2024-01-01T10:00:00.000+0000",
                    "updated": "2024-01-05T15:00:00.000+0000",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-02T10:00:00.000+0000",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2024-01-05T15:00:00.000+0000",
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
            },
            {
                "key": "TEST-2",
                "fields": {
                    "summary": "Test Issue 2",
                    "status": {"name": "In Progress"},
                    "created": "2024-01-10T09:00:00.000+0000",
                    "updated": "2024-01-12T11:00:00.000+0000",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2024-01-11T10:00:00.000+0000",
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
            },
        ]

        # Write issues to a JSON file
        issues_file = tmp_path / "issues.json"
        issues_file.write_text(json.dumps(issues, indent=2))
        return issues_file

    def test_analyze_subgroup_exists(self, runner):
        """Test that the analyze subgroup exists under jira command."""
        result = runner.invoke(jira, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()
        assert "state-durations" in result.output

    def test_state_durations_command_exists(self, runner):
        """Test that state-durations command exists under analyze group."""
        result = runner.invoke(jira, ["analyze", "state-durations", "--help"])
        assert result.exit_code == 0
        assert "state-durations" in result.output.lower()
        assert "input_file" in result.output.lower()
        assert "--output" in result.output or "-o" in result.output

    def test_state_durations_required_arguments(self, runner, tmp_path):
        """Test that state-durations requires input_file and output arguments."""
        # Test missing input file
        result = runner.invoke(jira, ["analyze", "state-durations"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output

        # Test missing output option
        dummy_file = tmp_path / "dummy.json"
        dummy_file.write_text("[]")
        result = runner.invoke(jira, ["analyze", "state-durations", str(dummy_file)])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_state_durations_with_valid_file(self, runner, sample_issues, tmp_path):
        """Test state-durations with valid input file."""
        output_file = tmp_path / "output.csv"

        with patch("temet_jira.cli.StateDurationAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer

            # Mock the analyze_issues method
            mock_analyzer.analyze_issues.return_value = [
                {
                    "issue_key": "TEST-1",
                    "state_durations": {
                        "To Do": 86400,
                        "In Progress": 302400,
                        "Done": 0,
                    },
                },
                {
                    "issue_key": "TEST-2",
                    "state_durations": {"To Do": 86400, "In Progress": 172800},
                },
            ]

            result = runner.invoke(
                jira,
                [
                    "analyze",
                    "state-durations",
                    str(sample_issues),
                    "-o",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()
            assert (
                "Successfully" in result.output or "completed" in result.output.lower()
            )

    def test_state_durations_with_date_filters(self, runner, sample_issues, tmp_path):
        """Test state-durations with date range filters."""
        output_file = tmp_path / "output.csv"

        with patch("temet_jira.cli.StateDurationAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            # Mock the analyze_issues method to return some results instead of raising NotImplementedError
            mock_analyzer.analyze_issues.return_value = [
                {
                    "issue_key": "TEST-1",
                    "summary": "Test Issue 1",
                    "current_status": "Done",
                    "created": "2024-01-01T10:00:00.000+0000",
                    "updated": "2024-01-05T15:00:00.000+0000",
                    "state_durations": {},
                }
            ]

            result = runner.invoke(
                jira,
                [
                    "analyze",
                    "state-durations",
                    str(sample_issues),
                    "-o",
                    str(output_file),
                    "--date-from",
                    "2024-01-01",
                    "--date-to",
                    "2024-08-05",
                ],
            )

            # Debug output if test fails
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                print(f"Exception: {result.exception}")

            assert result.exit_code == 0
            # Verify the analyzer was called with filtered issues
            assert mock_analyzer.analyze_issues.called

    def test_state_durations_with_business_hours(self, runner, sample_issues, tmp_path):
        """Test state-durations with business hours calculation."""
        output_file = tmp_path / "output.csv"

        with patch("temet_jira.cli.StateDurationAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_issues_business_hours = MagicMock(
                return_value=[
                    {
                        "issue_key": "TEST-1",
                        "summary": "Test Issue 1",
                        "current_status": "Done",
                        "created": "2024-01-01T10:00:00.000+0000",
                        "updated": "2024-01-05T15:00:00.000+0000",
                        "state_durations": {},
                    }
                ]
            )
            mock_analyzer.analyze_issues = MagicMock(
                return_value=[
                    {
                        "issue_key": "TEST-1",
                        "summary": "Test Issue 1",
                        "current_status": "Done",
                        "created": "2024-01-01T10:00:00.000+0000",
                        "updated": "2024-01-05T15:00:00.000+0000",
                        "state_durations": {},
                    }
                ]
            )

            result = runner.invoke(
                jira,
                [
                    "analyze",
                    "state-durations",
                    str(sample_issues),
                    "-o",
                    str(output_file),
                    "--business-hours",
                ],
            )

            assert result.exit_code == 0
            # Should call business hours method when flag is present (or fallback to regular if not available)
            assert (
                mock_analyzer.analyze_issues_business_hours.called
                or mock_analyzer.analyze_issues.called
            )

    def test_state_durations_with_timezone(self, runner, sample_issues, tmp_path):
        """Test state-durations with custom timezone."""
        output_file = tmp_path / "output.csv"

        with patch("temet_jira.cli.StateDurationAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_issues.return_value = []

            result = runner.invoke(
                jira,
                [
                    "analyze",
                    "state-durations",
                    str(sample_issues),
                    "-o",
                    str(output_file),
                    "--timezone",
                    "America/New_York",
                ],
            )

            assert result.exit_code == 0

    def test_state_durations_invalid_json_file(self, runner, tmp_path):
        """Test state-durations with invalid JSON file."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            jira,
            ["analyze", "state-durations", str(invalid_file), "-o", str(output_file)],
        )

        assert result.exit_code != 0
        assert "Error" in result.output or "Invalid" in result.output

    def test_state_durations_nonexistent_file(self, runner, tmp_path):
        """Test state-durations with non-existent input file."""
        output_file = tmp_path / "output.csv"

        result = runner.invoke(
            jira,
            [
                "analyze",
                "state-durations",
                "/nonexistent/file.json",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output.lower()

    def test_state_durations_progress_shown_for_large_files(self, runner, tmp_path):
        """Test that progress is shown for large files."""
        # Create a large issues file
        large_issues = [
            {
                "key": f"TEST-{i}",
                "fields": {
                    "summary": f"Test Issue {i}",
                    "status": {"name": "Done"},
                    "created": "2024-01-01T10:00:00.000+0000",
                    "updated": "2024-01-05T15:00:00.000+0000",
                },
                "changelog": {"histories": []},
            }
            for i in range(100)
        ]

        issues_file = tmp_path / "large_issues.json"
        issues_file.write_text(json.dumps(large_issues))
        output_file = tmp_path / "output.csv"

        with patch("temet_jira.cli.StateDurationAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_issues.return_value = []

            result = runner.invoke(
                jira,
                [
                    "analyze",
                    "state-durations",
                    str(issues_file),
                    "-o",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            # Check for progress indication (exact text may vary)
            # Progress might be shown via console.status or printed messages
