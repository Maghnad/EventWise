"""HTML and Free-Text Sanitization Utility for XSS Prevention.

Uses ``bleach`` to strip dangerous HTML, script tags, javascript: URIs,
and inline event handlers from all user-submitted text fields before persistence.
"""

from __future__ import annotations

import bleach


def sanitize_text(value: str | None) -> str | None:
    """Sanitize a free-text string by stripping all HTML tags and dangerous markup.

    Args:
        value: Raw text input from user.

    Returns:
        Cleaned string with all HTML tags stripped and entities safe,
        or None if input was None.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return [sanitize_text(item) for item in value if item is not None]  # type: ignore[return-value]
    if not isinstance(value, str):
        return value

    # Completely strip all HTML tags and attributes
    cleaned: str = bleach.clean(
        value,
        tags=[],
        attributes={},
        strip=True,
    )
    return cleaned.strip()


def sanitize_list(values: list[str] | None) -> list[str]:
    """Sanitize a list of strings."""
    if not values:
        return []
    return [sanitize_text(v) or v for v in values if v is not None]
