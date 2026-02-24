"""Access control for table-level query restrictions."""

from __future__ import annotations


def is_table_allowed(table_name: str, allowed_tables: list[str]) -> bool:
    """Check if a table name is in the allowed tables list.

    Args:
        table_name: The table name to check.
        allowed_tables: List of permitted table names.

    Returns:
        True if the table is allowed, False otherwise.
    """
    return table_name in allowed_tables
