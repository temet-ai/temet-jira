"""Configuration management for jira-tool.

Supports global config file (~/.config/jira-tool/config.yaml) with fallback to environment variables.
"""

import os
from pathlib import Path
from typing import Any

import yaml

# Config file location (follows XDG Base Directory spec)
CONFIG_DIR = Path.home() / ".config" / "jira-tool"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Valid configuration keys
VALID_KEYS = {
    "base_url": "Jira instance URL (e.g., https://company.atlassian.net)",
    "username": "Your email address for Jira",
    "api_token": "API token from Atlassian account settings",
    "project": "Project key (e.g., PROJ)",
    "component": "Component filter",
    "max_results": "Max results per query (default: 300)",
}

# Mapping from config keys to environment variable names
ENV_VAR_MAP = {
    "base_url": "JIRA_BASE_URL",
    "username": "JIRA_USERNAME",
    "api_token": "JIRA_API_TOKEN",
    "project": "JIRA_DEFAULT_PROJECT",
    "component": "JIRA_DEFAULT_COMPONENT",
    "max_results": "JIRA_DEFAULT_MAX_RESULTS",
}


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_FILE


def config_exists() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()


def load_config() -> dict[str, Any]:
    """Load configuration from file.

    Returns:
        Dictionary of configuration values, empty dict if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except (yaml.YAMLError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config: Dictionary of configuration values to save.
    """
    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Set restrictive permissions on config file (contains secrets)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Make file readable only by owner (0600)
    CONFIG_FILE.chmod(0o600)


def get_value(key: str) -> str | None:
    """Get a configuration value.

    Priority order:
    1. Environment variable
    2. Config file

    Args:
        key: Configuration key (e.g., 'base_url')

    Returns:
        Configuration value or None if not set.
    """
    # Check environment variable first
    env_var = ENV_VAR_MAP.get(key)
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value

    # Fall back to config file
    config = load_config()
    return config.get(key)


def set_value(key: str, value: str) -> None:
    """Set a configuration value in the config file.

    Args:
        key: Configuration key
        value: Value to set

    Raises:
        ValueError: If key is not a valid configuration key.
    """
    if key not in VALID_KEYS:
        raise ValueError(f"Invalid config key: {key}. Valid keys: {', '.join(VALID_KEYS.keys())}")

    config = load_config()
    config[key] = value
    save_config(config)


def delete_value(key: str) -> bool:
    """Delete a configuration value from the config file.

    Args:
        key: Configuration key to delete

    Returns:
        True if key was deleted, False if it didn't exist.
    """
    config = load_config()
    if key in config:
        del config[key]
        save_config(config)
        return True
    return False


def get_all_config() -> dict[str, dict[str, Any]]:
    """Get all configuration values with their sources.

    Returns:
        Dictionary mapping keys to {value, source} dicts.
    """
    file_config = load_config()
    result = {}

    for key in VALID_KEYS:
        env_var = ENV_VAR_MAP.get(key)
        env_value = os.environ.get(env_var) if env_var else None
        file_value = file_config.get(key)

        if env_value:
            result[key] = {"value": env_value, "source": f"env ({env_var})"}
        elif file_value:
            result[key] = {"value": file_value, "source": "config file"}
        else:
            result[key] = {"value": None, "source": "not set"}

    return result


def is_configured() -> bool:
    """Check if the minimum required configuration is present.

    Returns:
        True if base_url, username, and api_token are all configured.
    """
    return all([
        get_value("base_url"),
        get_value("username"),
        get_value("api_token"),
    ])


def mask_sensitive(value: str | None, key: str) -> str:
    """Mask sensitive values for display.

    Args:
        value: The value to potentially mask
        key: The config key (to determine if sensitive)

    Returns:
        Masked or original value.
    """
    if value is None:
        return "(not set)"

    if key == "api_token":
        if len(value) > 8:
            return value[:4] + "*" * (len(value) - 8) + value[-4:]
        return "*" * len(value)

    return value
