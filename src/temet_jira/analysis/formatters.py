"""Formatters for state duration analysis output."""

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from typing import Any


class FormatterError(Exception):
    """Base exception for formatter errors."""

    pass


class DataSerializationError(FormatterError):
    """Raised when data cannot be serialized."""

    pass


def _json_default_serializer(obj: Any) -> Any:
    """Custom JSON serializer for non-standard types.

    Args:
        obj: Object to serialize.

    Returns:
        JSON-serializable representation of the object.

    Raises:
        TypeError: If object cannot be serialized.
    """
    # Handle datetime objects
    if isinstance(obj, datetime | date):
        return obj.isoformat()

    # Handle Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # Handle bytes
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            return repr(obj)

    # Handle sets
    if isinstance(obj, set):
        return list(obj)

    # Handle objects with __dict__ (but check if it's not empty or None)
    if hasattr(obj, "__dict__") and obj.__dict__:
        return obj.__dict__

    # Fall back to string representation
    return str(obj)


def _sanitize_special_floats(obj: Any) -> Any:
    """Recursively sanitize special float values in data structures.

    Args:
        obj: Object to sanitize.

    Returns:
        Sanitized object with NaN/Infinity replaced with None.
    """
    if isinstance(obj, float):
        if obj != obj or obj == float("inf") or obj == float("-inf"):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _sanitize_special_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_special_floats(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_sanitize_special_floats(item) for item in obj)
    return obj


def format_as_json(
    issues: list[dict[str, Any]], indent: int | None = 2, sort_keys: bool = False
) -> str:
    """Format Jira issues as JSON.

    Accepts a list of Jira issues and returns formatted JSON string.
    Handles nested data structures properly and non-serializable data gracefully.

    Args:
        issues: List of Jira issue dictionaries.
        indent: Number of spaces for JSON indentation. None for compact mode.
        sort_keys: Whether to sort dictionary keys alphabetically.

    Returns:
        JSON string representation of the issues.

    Raises:
        FormatterError: For unrecoverable formatting issues.

    Example:
        >>> issues = [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        >>> result = format_as_json(issues, indent=2)
        >>> print(result)
        [
          {
            "key": "PROJ-123",
            "fields": {
              "summary": "Test"
            }
          }
        ]
    """
    try:
        # Pre-process to handle special float values
        # This may raise RecursionError if there are circular references
        try:
            sanitized_issues = _sanitize_special_floats(issues)
        except RecursionError:
            # Circular reference detected during sanitization
            raise ValueError("Circular reference detected") from None

        # Check for circular references by attempting serialization
        # The json module will raise ValueError for circular references
        result = json.dumps(
            sanitized_issues,
            indent=indent,
            sort_keys=sort_keys,
            default=_json_default_serializer,
            ensure_ascii=False,
        )
        return result
    except ValueError as e:
        if "circular reference" in str(e).lower() or "Circular reference" in str(e):
            raise ValueError("Circular reference detected") from None
        # Re-raise if it's already our circular reference error
        if str(e) == "Circular reference detected":
            raise
        # Re-raise other ValueError instances
        raise DataSerializationError(f"Failed to serialize data: {e}") from e
    except TypeError as e:
        # This shouldn't happen with our custom serializer, but just in case
        raise DataSerializationError(f"Type error during serialization: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors
        raise FormatterError(f"Unexpected error during JSON formatting: {e}") from e


def format_as_jsonl(issues: list[dict[str, Any]], sort_keys: bool = False) -> str:
    """Format Jira issues as JSONL (JSON Lines).

    Each issue is serialized as a single line of JSON, with newlines between issues.
    This format is useful for streaming processing and line-by-line parsing.

    Args:
        issues: List of Jira issue dictionaries.
        sort_keys: Whether to sort dictionary keys alphabetically.

    Returns:
        JSONL string representation of the issues (one JSON object per line).

    Raises:
        FormatterError: For unrecoverable formatting issues.

    Example:
        >>> issues = [{"key": "PROJ-123", "fields": {"summary": "Test"}}]
        >>> result = format_as_jsonl(issues)
        >>> print(result)
        {"key":"PROJ-123","fields":{"summary":"Test"}}
    """
    try:
        # Pre-process to handle special float values
        try:
            sanitized_issues = _sanitize_special_floats(issues)
        except RecursionError:
            raise ValueError("Circular reference detected") from None

        # Serialize each issue as a single line
        lines = []
        for issue in sanitized_issues:
            try:
                line = json.dumps(
                    issue,
                    sort_keys=sort_keys,
                    default=_json_default_serializer,
                    ensure_ascii=False,
                    separators=(",", ":"),  # Compact format
                )
                lines.append(line)
            except ValueError as e:
                if "circular reference" in str(e).lower():
                    raise ValueError("Circular reference detected") from None
                raise DataSerializationError(f"Failed to serialize issue: {e}") from e
            except TypeError as e:
                raise DataSerializationError(
                    f"Type error during serialization: {e}"
                ) from e

        return "\n".join(lines)

    except ValueError as e:
        if str(e) == "Circular reference detected":
            raise
        raise DataSerializationError(f"Failed to serialize data: {e}") from e
    except Exception as e:
        raise FormatterError(f"Unexpected error during JSONL formatting: {e}") from e


def flatten_dict(
    data: dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
    max_depth: int = 5,
    current_depth: int = 0,
) -> dict[str, Any]:
    """Flatten a nested dictionary using dot notation.

    Args:
        data: Dictionary to flatten.
        parent_key: Parent key prefix for nested values.
        separator: Separator for nested keys.
        max_depth: Maximum depth to flatten.
        current_depth: Current recursion depth.

    Returns:
        Flattened dictionary with dot-notation keys.
    """
    items = []

    if current_depth >= max_depth:
        # If we've reached max depth, stringify the remaining structure
        return {parent_key: str(data)} if parent_key else {}

    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if value is None:
            items.append((new_key, ""))
        elif isinstance(value, dict):
            # Recursively flatten nested dictionaries
            items.extend(
                flatten_dict(
                    value,
                    new_key,
                    separator,
                    max_depth,
                    current_depth + 1,
                ).items()
            )
        elif isinstance(value, list):
            # Handle lists specially
            if not value:
                items.append((new_key, ""))
            else:
                # Check if it's a list of objects with specific keys to extract
                if all(isinstance(item, dict) for item in value):
                    # For lists of dicts, extract specific fields
                    extracted_values = []
                    for item in value:
                        # Try common field names
                        if "name" in item:
                            extracted_values.append(item["name"])
                        elif "filename" in item:
                            extracted_values.append(item["filename"])
                        elif "displayName" in item:
                            extracted_values.append(item["displayName"])
                        else:
                            # Fall back to first string value or string representation
                            for v in item.values():
                                if isinstance(v, str):
                                    extracted_values.append(v)
                                    break
                            else:
                                extracted_values.append(str(item))
                    items.append((new_key, ";".join(str(v) for v in extracted_values)))
                else:
                    # For lists of primitives, join with semicolon
                    items.append((new_key, ";".join(str(v) for v in value)))
        elif isinstance(value, bool | int | float | Decimal):
            items.append((new_key, str(value)))
        elif isinstance(value, datetime | date):
            items.append((new_key, value.isoformat()))
        else:
            items.append((new_key, str(value)))

    return dict(items)


def protect_csv_injection(value: str) -> str:
    """Protect against CSV injection attacks.

    Args:
        value: Cell value to protect.

    Returns:
        Protected value with prefix if needed.
    """
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def format_as_csv(
    issues: list[dict[str, Any]],
    delimiter: str = ",",
    include_headers: bool = True,
) -> str:
    """Format Jira issues as CSV with flattened structure.

    Args:
        issues: List of Jira issue dictionaries.
        delimiter: CSV delimiter character.
        include_headers: Whether to include header row.

    Returns:
        CSV string representation of the issues.
    """
    if not issues:
        return ""

    # Flatten all issues
    flattened_issues = [flatten_dict(issue) for issue in issues]

    # Collect all unique keys across all issues
    all_keys: set[str] = set()
    for issue in flattened_issues:
        all_keys.update(issue.keys())

    # Sort keys for consistent column order
    fieldnames = sorted(all_keys)

    # Create CSV output
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        delimiter=delimiter,
        extrasaction="ignore",
    )

    if include_headers:
        writer.writeheader()

    # Write rows with CSV injection protection
    for issue in flattened_issues:
        # Apply CSV injection protection to all string values
        protected_issue = {}
        for key in fieldnames:
            value = issue.get(key, "")
            if isinstance(value, str):
                value = protect_csv_injection(value)
            protected_issue[key] = value

        writer.writerow(protected_issue)

    return output.getvalue()


def format_as_table(
    _analysis_results: list[dict[str, Any]], max_width: int | None = None
) -> str:
    """Format state duration analysis results as a text table.

    Args:
        _analysis_results: List of analysis results from StateDurationAnalyzer.
        _max_width: Maximum width for the table output.

    Returns:
        Formatted table string representation of the analysis results.
    """
    # Implementation will be added in later tasks
    # This is an additional formatter that might be useful
    raise NotImplementedError("Table formatting implementation pending")


def format_duration(hours: float) -> str:
    """Format duration in hours to human-readable string.

    Args:
        hours: Duration in hours.

    Returns:
        Human-readable duration string (e.g., "2d 3h 15m").
    """
    # Implementation will be added in later tasks
    days = int(hours // 24)
    remaining_hours = int(hours % 24)
    minutes = int((hours % 1) * 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if remaining_hours > 0:
        parts.append(f"{remaining_hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "0m"
