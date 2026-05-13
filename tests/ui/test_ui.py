import os
from unittest.mock import patch

import pytest


class TestIsInteractive:
    def test_returns_false_when_ci_set(self, monkeypatch):
        monkeypatch.setenv("CI", "true")
        monkeypatch.delenv("JIRA_NO_INTERACTIVE", raising=False)
        monkeypatch.delenv("NO_INTERACTIVE", raising=False)
        from temet_jira.ui.console import is_interactive
        assert is_interactive() is False

    def test_returns_false_when_jira_no_interactive_set(self, monkeypatch):
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setenv("JIRA_NO_INTERACTIVE", "1")
        monkeypatch.delenv("NO_INTERACTIVE", raising=False)
        from temet_jira.ui.console import is_interactive
        assert is_interactive() is False

    def test_returns_false_when_no_interactive_set(self, monkeypatch):
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("JIRA_NO_INTERACTIVE", raising=False)
        monkeypatch.setenv("NO_INTERACTIVE", "1")
        from temet_jira.ui.console import is_interactive
        assert is_interactive() is False

    def test_returns_false_when_not_tty(self, monkeypatch):
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("JIRA_NO_INTERACTIVE", raising=False)
        monkeypatch.delenv("NO_INTERACTIVE", raising=False)
        from temet_jira.ui.console import is_interactive
        # pytest runs without a TTY, so this should be False
        assert is_interactive() is False


class TestFormatStatus:
    def test_todo_category(self):
        from temet_jira.ui.status import format_status
        result = format_status("To Do", "new")
        assert "[status.todo]" in result
        assert "To Do" in result

    def test_inprogress_category(self):
        from temet_jira.ui.status import format_status
        result = format_status("In Progress", "indeterminate")
        assert "[status.inprogress]" in result

    def test_done_category(self):
        from temet_jira.ui.status import format_status
        result = format_status("Done", "done")
        assert "[status.done]" in result

    def test_blocked_status_name(self):
        from temet_jira.ui.status import format_status
        result = format_status("Blocked")
        assert "[status.blocked]" in result

    def test_fallback_inprogress_from_name(self):
        from temet_jira.ui.status import format_status
        result = format_status("In Review")
        assert "[status.inprogress]" in result

    def test_fallback_done_from_name(self):
        from temet_jira.ui.status import format_status
        result = format_status("Closed")
        assert "[status.done]" in result

    def test_unknown_defaults_to_todo(self):
        from temet_jira.ui.status import format_status
        result = format_status("Backlog")
        assert "[status.todo]" in result


class TestNumberedFallback:
    def test_returns_correct_choice(self):
        from temet_jira.ui.prompts import _numbered_fallback
        with patch("click.prompt", return_value="2"), \
             patch("click.echo"):
            result = _numbered_fallback("Pick one", ["Alpha", "Beta", "Gamma"], None, allow_skip=False)
        assert result == "Beta"

    def test_skip_returns_none(self):
        from temet_jira.ui.prompts import _numbered_fallback
        with patch("click.prompt", return_value="0"), \
             patch("click.echo"):
            result = _numbered_fallback("Pick one", ["Alpha", "Beta"], None, allow_skip=True)
        assert result is None

    def test_literal_value_accepted(self):
        from temet_jira.ui.prompts import _numbered_fallback
        with patch("click.prompt", return_value="Alpha"), \
             patch("click.echo"):
            result = _numbered_fallback("Pick one", ["Alpha", "Beta"], None, allow_skip=False)
        assert result == "Alpha"


class TestNumberedMultiFallback:
    def test_empty_on_zero_input(self):
        from temet_jira.ui.prompts import _numbered_multi_fallback
        with patch("click.prompt", return_value="0"), \
             patch("click.echo"):
            result = _numbered_multi_fallback("Pick items", ["A", "B", "C"])
        assert result == []

    def test_selects_item_then_done(self):
        from temet_jira.ui.prompts import _numbered_multi_fallback
        with patch("click.prompt", side_effect=["1", "0"]), \
             patch("click.echo"):
            result = _numbered_multi_fallback("Pick items", ["A", "B", "C"])
        assert result == ["A"]
