"""Service for schema discovery — list tables and describe columns."""

from __future__ import annotations

import psycopg

LIST_TABLES_QUERY = """
SELECT
    t.table_name,
    t.table_schema,
    pg_stat.n_live_tup AS estimated_rows
FROM information_schema.tables t
LEFT JOIN pg_stat_user_tables pg_stat
    ON t.table_schema = pg_stat.schemaname
    AND t.table_name = pg_stat.relname
WHERE t.table_schema = %s
    AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name
"""

DESCRIBE_TABLE_QUERY = """
SELECT
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    c.udt_name
FROM information_schema.columns c
WHERE c.table_schema = %s
    AND c.table_name = %s
ORDER BY c.ordinal_position
"""

SPATIAL_COLUMNS_QUERY = """
SELECT
    f_geometry_column,
    type,
    srid,
    coord_dimension
FROM geometry_columns
WHERE f_table_schema = %s
    AND f_table_name = %s
"""


async def list_tables(
    conn: psycopg.AsyncConnection,
    schema: str,
    allowed_tables: list[str],
) -> list[dict[str, object]]:
    """List all allowed tables in the given schema.

    Returns only tables that are in the allowed_tables list.
    """
    async with conn.cursor() as cur:
        await cur.execute(LIST_TABLES_QUERY, (schema,))
        rows = await cur.fetchall()

    return [
        {
            "table_name": row[0],
            "schema": row[1],
            "estimated_rows": row[2] or 0,
        }
        for row in rows
        if row[0] in allowed_tables
    ]


async def describe_table(
    conn: psycopg.AsyncConnection,
    schema: str,
    table_name: str,
) -> list[dict[str, object]]:
    """Get column details for a table."""
    async with conn.cursor() as cur:
        await cur.execute(DESCRIBE_TABLE_QUERY, (schema, table_name))
        column_rows = await cur.fetchall()

    spatial_info: dict[str, dict[str, object]] = {}
    try:
        async with conn.cursor() as cur:
            await cur.execute(SPATIAL_COLUMNS_QUERY, (schema, table_name))
            for row in await cur.fetchall():
                spatial_info[row[0]] = {
                    "geometry_type": row[1],
                    "srid": row[2],
                    "coord_dimension": row[3],
                }
    except psycopg.errors.UndefinedTable:
        pass

    columns = []
    for row in column_rows:
        col: dict[str, object] = {
            "column_name": row[0],
            "data_type": row[1],
            "is_nullable": row[2] == "YES",
            "column_default": row[3],
        }
        if row[0] in spatial_info:
            col.update(spatial_info[row[0]])
        columns.append(col)

    return columns
