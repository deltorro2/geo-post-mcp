"""Access control for table-level query restrictions."""

from __future__ import annotations


def is_table_allowed(table_name: str, schema: str, allowed_tables: list[str]) -> bool:
    """Check if a table name is in the allowed tables list.

    Args:
        table_name: The table name to check.
        schema: The schema name to qualify the table.
        allowed_tables: List of permitted schema-qualified table names (e.g. 'remez1.polygons').

    Returns:
        True if the table is allowed, False otherwise.
    """
    qualified_name = f"{schema}.{table_name}"
    return qualified_name in allowed_tables

