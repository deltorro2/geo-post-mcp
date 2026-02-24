"""Service for querying column metadata (field meanings) from PostgreSQL catalog."""

from __future__ import annotations

import psycopg

from src.models.fieldmeaning import FieldMeaningEntry

COLUMN_QUERY = """
SELECT
    c.column_name,
    c.data_type,
    c.ordinal_position,
    pgd.description
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st
    ON c.table_schema = st.schemaname
    AND c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid
    AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema = %s
    AND c.table_name = %s
ORDER BY c.ordinal_position
"""

TABLE_EXISTS_QUERY = """
SELECT 1 FROM information_schema.tables
WHERE table_schema = %s AND table_name = %s
"""


async def check_table_exists(
    conn: psycopg.AsyncConnection,
    schema: str,
    table_name: str,
) -> bool:
    """Check if a table exists in the given schema."""
    async with conn.cursor() as cur:
        await cur.execute(TABLE_EXISTS_QUERY, (schema, table_name))
        row = await cur.fetchone()
        return row is not None


async def get_field_meanings(
    conn: psycopg.AsyncConnection,
    schema: str,
    table_name: str,
) -> list[FieldMeaningEntry]:
    """Query column metadata for a table.

    Args:
        conn: Database connection.
        schema: Schema name.
        table_name: Table name (bare, no schema qualifier).

    Returns:
        List of FieldMeaningEntry sorted by ordinal position.
    """
    async with conn.cursor() as cur:
        await cur.execute(COLUMN_QUERY, (schema, table_name))
        rows = await cur.fetchall()

    return [
        FieldMeaningEntry(
            column_name=row[0],
            data_type=row[1],
            ordinal_position=row[2],
            description=row[3],
        )
        for row in rows
    ]
