"""Configuration management for temet-jira.

The config file (~/.config/temet-jira/config.yaml) is the single source of truth.
Values may contain ${VAR_NAME} references resolved from the environment at read time —
this is an explicit user choice, not an implicit fallback.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml


def _interpolate(value: str) -> str:
    """Resolve ${VAR_NAME} or $VAR_NAME references in a config value."""
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        var_name = m.group(1) or m.group(2)
        return os.environ.get(var_name, m.group(0))
    return re.sub(r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)', _replace, value)


# Matches a bare $VAR or ${VAR} that is the entire value
_BARE_ENV_REF_RE = re.compile(r'^\$\{?([A-Z_][A-Z0-9_]*)\}?$')


def normalize_env_ref(value: str) -> tuple[str, str | None]:
    """Normalize a bare env var reference to canonical ${VAR} form.

    Returns (normalized_value, var_name_if_detected).
    - ``$VAR``   → ``${VAR}``, var_name = "VAR"
    - ``${VAR}`` → ``${VAR}``, var_name = "VAR"
    - anything else → unchanged, var_name = None
    """
    m = _BARE_ENV_REF_RE.match(value.strip())
    if m:
        var_name = m.group(1)
        return f"${{{var_name}}}", var_name
    return value, None


# Config file location (follows XDG Base Directory spec)
CONFIG_DIR = Path.home() / ".config" / "temet-jira"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Valid configuration keys
VALID_KEYS = {
    "base_url": "Jira instance URL (e.g., https://company.atlassian.net)",
    "username": "Your email address for Jira",
    "api_token": "API token from Atlassian account settings",
    "project": "Project key (e.g., PROJ)",
    "component": "Component filter",
    "max_results": "Max results per query (default: 300)",
    "default_format": "Default output format: table, json, jsonl, csv (default: table)",
}

# Per-key validation: (hint, regex that a valid value must match)
_KEY_VALIDATORS: dict[str, tuple[str, re.Pattern[str]]] = {
    "base_url": (
        "must be a URL starting with https:// or a ${VAR} reference",
        re.compile(r"^https?://|\$\{"),
    ),
    "default_format": (
        "must be one of: table, json, jsonl, csv",
        re.compile(r"^(table|json|jsonl|csv|\$\{)"),
    ),
}

# Used only by the setup command to suggest env var values to the user
ENV_VAR_MAP = {
    "base_url": "JIRA_BASE_URL",
    "username": "JIRA_USERNAME",
    "api_token": "JIRA_API_TOKEN",
    "project": "JIRA_DEFAULT_PROJECT",
    "component": "JIRA_DEFAULT_COMPONENT",
    "max_results": "JIRA_DEFAULT_MAX_RESULTS",
    "default_format": "JIRA_DEFAULT_FORMAT",
}

_VALID_FORMATS = {"table", "json", "jsonl", "csv"}


def validate_value(key: str, value: str) -> str | None:
    """Validate a config value for the given key.

    Returns an error message string if invalid, None if valid.
    """
    if key not in VALID_KEYS:
        valid = ", ".join(VALID_KEYS)
        return f"Unknown key '{key}'. Valid keys: {valid}"
    if not value.strip():
        return f"Value for '{key}' cannot be empty"
    if key in _KEY_VALIDATORS:
        hint, pattern = _KEY_VALIDATORS[key]
        if not pattern.search(value):
            return f"Invalid value for '{key}': {hint}. Got: {value!r}"
    return None


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_FILE


def config_exists() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except (yaml.YAMLError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    CONFIG_FILE.chmod(0o600)


def get_value(key: str) -> str | None:
    """Get a configuration value from the config file.

    Config file is the single source of truth. Values stored as ${VAR}
    references are resolved from the environment at read time.

    Returns None if the key is not set in the config file.
    """
    config = load_config()
    raw = config.get(key)
    if raw is None:
        return None
    resolved = _interpolate(str(raw))
    return resolved if resolved else None


def get_all_config() -> dict[str, str | None]:
    """Get all configuration values from the config file.

    Returns a dict of key → resolved value (None if not set).
    """
    config = load_config()
    result: dict[str, str | None] = {}
    for key in VALID_KEYS:
        raw = config.get(key)
        if raw is not None:
            resolved = _interpolate(str(raw))
            result[key] = resolved if resolved else None
        else:
            result[key] = None
    return result


def get_default_format() -> str:
    """Return the configured default output format.

    Reads from config file. Falls back to 'jsonl' when stdout is not a TTY,
    'table' otherwise.
    """
    import sys

    raw = load_config().get("default_format")
    if raw:
        value = _interpolate(str(raw)).lower()
        if value in _VALID_FORMATS:
            return value

    return "jsonl" if not sys.stdout.isatty() else "table"


def set_value(key: str, value: str) -> None:
    """Set a configuration value in the config file.

    Raises:
        ValueError: If key is invalid or value fails validation.
    """
    error = validate_value(key, value)
    if error:
        raise ValueError(error)
    config = load_config()
    config[key] = value
    save_config(config)


def delete_value(key: str) -> bool:
    """Delete a configuration value from the config file.

    Returns True if the key was deleted, False if it didn't exist.
    """
    config = load_config()
    if key in config:
        del config[key]
        save_config(config)
        return True
    return False


def is_configured() -> bool:
    """Check if the minimum required configuration is present.

    Returns True if base_url, username, and api_token are all set in config.
    """
    return all([
        get_value("base_url"),
        get_value("username"),
        get_value("api_token"),
    ])


def mask_sensitive(value: str | None, key: str) -> str:
    """Mask sensitive values for display."""
    if value is None:
        return "(not set)"
    if key == "api_token":
        if len(value) > 8:
            return value[:4] + "*" * (len(value) - 8) + value[-4:]
        return "*" * len(value)
    return value


def _project_meta_path(project_key: str) -> Path:
    return CONFIG_DIR / f"project-{project_key.upper()}.yaml"


def load_project_meta(project_key: str) -> dict[str, Any]:
    """Load cached project metadata (components, labels, issue types)."""
    path = _project_meta_path(project_key)
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}


def save_project_meta(project_key: str, meta: dict[str, Any]) -> Path:
    """Save project metadata to per-project cache file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _project_meta_path(project_key)
    with open(path, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, sort_keys=False)
    return path
