"""
Utility helper functions for common operations.

This module provides reusable utility functions to reduce code duplication
across the application.
"""

import io


def normalize_hex_color(value: str | None) -> str | None:
    """
    Validate and normalise a hex colour string.

    Accepts values with or without a leading '#'. Returns the 6-digit
    uppercase hex string (without '#') if valid, or ``None`` if the
    input is missing or malformed.

    Example:
        >>> normalize_hex_color("#2f5597")
        '2F5597'
        >>> normalize_hex_color("gg0000")
        None
    """
    if not value:
        return None
    cleaned = str(value).strip().replace("#", "")
    if len(cleaned) != 6:
        return None
    try:
        int(cleaned, 16)
    except ValueError:
        return None
    return cleaned.upper()


def reset_buffer(buffer: io.BytesIO) -> io.BytesIO:
    """
    Reset a BytesIO buffer to the beginning.

    Args:
        buffer: BytesIO buffer to reset

    Returns:
        The same buffer (for chaining)

    Example:
        >>> buf = io.BytesIO(b"data")
        >>> buf.read()  # reads all data
        >>> reset_buffer(buf)  # reset to start
        >>> buf.read()  # can read again
    """
    buffer.seek(0)
    return buffer


def filter_display_columns(columns: list[str]) -> list[str]:
    """
    Filter out internal columns (like Separator) from display.

    Used by UI components to show only user-relevant columns.

    Args:
        columns: List of column names

    Returns:
        Filtered list excluding internal columns

    Example:
        >>> cols = ['Time', 'Load', 'Separator', 'Stress']
        >>> filter_display_columns(cols)
        ['Time', 'Load', 'Stress']
    """
    # Columns to exclude from display (case-insensitive)
    internal_columns = {"separator"}

    return [col for col in columns if col.lower() not in internal_columns]
