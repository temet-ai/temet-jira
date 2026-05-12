"""Tests for type profiles and profile lookup."""

from temet_jira.document.builders.profiles import (
    EMOJI_MAP,
    FIELD_LABELS,
    TYPE_PROFILES,
    get_profile,
)


def test_get_profile_known_type() -> None:
    """Known types return their specific profile."""
    profile = get_profile("epic")
    assert profile["emoji"] == "rocket"
    assert "priority" in profile["header_fields"]
    assert "description" in profile["sections"]


def test_get_profile_risk() -> None:
    """Risk type has risk-specific sections."""
    profile = get_profile("risk")
    assert profile["emoji"] == "warning"
    assert "risk_assessment" in profile["sections"]
    assert "monitoring_plan" in profile["sections"]
    assert profile["header_panel_type"] == "warning"


def test_get_profile_case_insensitive() -> None:
    """Profile lookup is case-insensitive."""
    assert get_profile("Epic") == get_profile("epic")
    assert get_profile("RISK") == get_profile("risk")
    assert get_profile("Sub-Task") == get_profile("sub-task")


def test_get_profile_unknown_returns_default() -> None:
    """Unknown types fall back to _default profile."""
    profile = get_profile("Unicorn")
    assert profile == TYPE_PROFILES["_default"]
    assert profile["emoji"] == "clipboard"


def test_all_profiles_have_required_keys() -> None:
    """Every profile must have emoji, header_fields, header_panel_type, sections."""
    required = {"emoji", "header_fields", "header_panel_type", "sections"}
    for name, profile in TYPE_PROFILES.items():
        missing = required - set(profile.keys())
        assert not missing, f"Profile '{name}' missing keys: {missing}"


def test_emoji_map_covers_all_profiles() -> None:
    """Every emoji string in profiles has a mapping in EMOJI_MAP."""
    for name, profile in TYPE_PROFILES.items():
        emoji_key = profile["emoji"]
        assert emoji_key in EMOJI_MAP, (
            f"Profile '{name}' uses emoji '{emoji_key}' not in EMOJI_MAP"
        )


def test_field_labels_cover_all_header_fields() -> None:
    """Every header field across all profiles has a label."""
    for name, profile in TYPE_PROFILES.items():
        for field in profile["header_fields"]:
            assert field in FIELD_LABELS, (
                f"Profile '{name}' header field '{field}' has no FIELD_LABELS entry"
            )
