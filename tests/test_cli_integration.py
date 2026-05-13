"""Integration tests for Jira CLI search command enhancements."""

from click.testing import CliRunner

from temet_jira.cli import jira


class TestJiraSearchIntegration:
    """Integration tests for enhanced Jira search functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_search_help_text(self):
        """Test that help text shows all new options."""
        result = self.runner.invoke(jira, ["search", "--help"])

        assert result.exit_code == 0

        # Check that all new options are documented in help
        assert "--fields" in result.output
        assert "fields to return" in result.output

        assert "--expand" in result.output
        assert "expand" in result.output.lower()

        assert "--output" in result.output
        assert "-o" in result.output
        assert "Output file path" in result.output

        assert "--format" in result.output
        assert "-f" in result.output
        assert "Output format" in result.output
        assert "json" in result.output
        assert "csv" in result.output
        assert "table" in result.output

        assert "--all" in result.output
        assert "Fetch all results" in result.output

    def test_format_option_choices(self):
        """Test that format option only accepts valid choices."""
        # Test invalid format
        result = self.runner.invoke(
            jira, ["search", "project = TEST", "--format", "xml"]
        )
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "xml" in result.output

        # Test valid formats don't cause error (will fail at client level, but parsing should succeed)
        for fmt in ["json", "csv", "table", "JSON", "CSV", "TABLE"]:
            result = self.runner.invoke(
                jira, ["search", "project = TEST", "--format", fmt]
            )
            # Should fail at JiraClient creation, not at option parsing
            assert "Invalid value" not in result.output

    def test_option_shortcuts(self):
        """Test that option shortcuts work correctly."""
        # Test -n for --max-results (existing)
        result = self.runner.invoke(jira, ["search", "--help"])
        assert "-n" in result.output
        assert "--max-results" in result.output

        # Test -o for --output
        assert "-o" in result.output
        assert "--output" in result.output

        # Test -f for --format
        assert "-f" in result.output
        assert "--format" in result.output

    def test_backwards_compatibility(self):
        """Test that existing command syntax still works."""
        # Original command should still work
        result = self.runner.invoke(jira, ["search", "project = TEST"])
        # Will fail at JiraClient creation, but should parse correctly
        assert "no such option" not in result.output.lower()

        result = self.runner.invoke(
            jira, ["search", "project = TEST", "--max-results", "20"]
        )
        assert "no such option" not in result.output.lower()

        result = self.runner.invoke(jira, ["search", "project = TEST", "-n", "20"])
        assert "no such option" not in result.output.lower()
