"""Type profiles for Jira issue types.

Each profile declares which sections a type uses, its header fields,
and display settings. Profiles drive the TypedBuilder.
"""

from typing import Any

# Emoji short names -> Unicode characters
EMOJI_MAP: dict[str, str] = {
    "rocket": "\U0001f680",      # 🚀
    "warning": "\u26a0\ufe0f",   # ⚠️
    "pushpin": "\U0001f4cc",     # 📌
    "clipboard": "\U0001f4cb",   # 📋
}

# Field name -> display label with emoji prefix
FIELD_LABELS: dict[str, str] = {
    "priority": "\u26a0\ufe0f Priority",         # ⚠️ Priority
    "dependencies": "\U0001f517 Dependencies",    # 🔗 Dependencies
    "services": "\u2699\ufe0f Services",          # ⚙️ Services
    "component": "\u2699\ufe0f Component",        # ⚙️ Component
    "story_points": "\U0001f4ca Story Points",    # 📊 Story Points
    "epic": "\U0001f517 Epic",                    # 🔗 Epic
    "parent": "\U0001f517 Parent",                # 🔗 Parent
    "estimated_hours": "\u23f1\ufe0f Estimate",   # ⏱️ Estimate
    "likelihood": "\U0001f4ca Likelihood",        # 📊 Likelihood
    "impact": "\U0001f4a5 Impact",                # 💥 Impact
    "overall_risk": "\u26a0\ufe0f Overall Risk",  # ⚠️ Overall Risk
}

TYPE_PROFILES: dict[str, dict[str, Any]] = {
    "epic": {
        "emoji": "rocket",
        "header_fields": ["priority", "dependencies", "services"],
        "header_panel_type": "warning",
        "sections": [
            "description",
            "problem_statement",
            "acceptance_criteria",
            "implementation_details",
            "edge_cases",
            "testing_considerations",
            "out_of_scope",
            "success_metrics",
        ],
    },
    "risk": {
        "emoji": "warning",
        "header_fields": ["likelihood", "impact", "overall_risk"],
        "header_panel_type": "warning",
        "sections": [
            "description",
            "risk_assessment",
            "mitigation",
            "acceptance_rationale",
            "acceptance_criteria",
            "monitoring_plan",
        ],
    },
    "sub-task": {
        "emoji": "pushpin",
        "header_fields": ["parent", "estimated_hours"],
        "header_panel_type": "info",
        "sections": [
            "description",
            "steps",
            "done_criteria",
        ],
    },
    "_default": {
        "emoji": "clipboard",
        "header_fields": ["component", "story_points", "epic"],
        "header_panel_type": "info",
        "sections": [
            "description",
            "implementation_details",
            "acceptance_criteria",
        ],
    },
}


def get_profile(issue_type: str) -> dict[str, Any]:
    """Get the profile for an issue type, falling back to _default.

    Lookup is case-insensitive.
    """
    return TYPE_PROFILES.get(issue_type.lower(), TYPE_PROFILES["_default"])
