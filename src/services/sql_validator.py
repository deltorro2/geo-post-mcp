"""SQL statement validator — ensures only SELECT queries are executed."""

from __future__ import annotations

import re


def validate_select_only(sql: str) -> None:
    """Validate that a SQL statement is a SELECT query.

    Strips leading comments and whitespace, then checks that the
    first keyword is SELECT or WITH (for CTEs).

    Args:
        sql: The SQL statement to validate.

    Raises:
        ValueError: If the statement is not a SELECT query.
    """
    cleaned = _strip_leading_comments(sql).strip()
    if not cleaned:
        raise ValueError("Empty SQL statement.")

    first_word = cleaned.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(
            f"Only SELECT queries are permitted. "
            f"Received statement starting with: {first_word}"
        )


def _strip_leading_comments(sql: str) -> str:
    """Remove leading SQL comments (-- and /* */ style)."""
    result = sql.strip()
    while True:
        if result.startswith("--"):
            newline = result.find("\n")
            if newline == -1:
                return ""
            result = result[newline + 1:].strip()
        elif result.startswith("/*"):
            end = result.find("*/")
            if end == -1:
                return ""
            result = result[end + 2:].strip()
        else:
            break
    return result
