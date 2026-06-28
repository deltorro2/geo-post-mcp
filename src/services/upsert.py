"""Service for upserting a single key/value pair into a table's metadata column.

This is the only write path in the server. It is deliberately limited to a
single atomic JSON-merge UPDATE on the ``metadata`` column of one record,
located by its ``id`` (always a ``bigint`` primary key).
"""

from __future__ import annotations

import time

import psycopg
import structlog
from psycopg import sql

logger = structlog.get_logger(__name__)

METADATA_COLUMN_QUERY = """
SELECT 1 FROM information_schema.columns
WHERE table_schema = %s AND table_name = %s AND column_name = 'metadata'
"""

# Atomic upsert: COALESCE handles NULL/absent metadata; the `||` operator
# inserts a new key or overwrites an existing key's value while preserving all
# other keys. The left operand is cast to jsonb so a `json`-typed column works
# too. {} is the schema-qualified table identifier.
_UPSERT_TEMPLATE = (
    "UPDATE {} "
    "SET metadata = COALESCE(metadata::jsonb, '{{}}'::jsonb) || %s::jsonb "
    "WHERE id = %s"
)


async def has_metadata_column(
    conn: psycopg.AsyncConnection,
    schema: str,
    table_name: str,
) -> bool:
    """Return True if the table has a ``metadata`` column.

    The ``id`` bigint primary key is guaranteed by database convention, so only
    the ``metadata`` column needs to be checked for eligibility.
    """
    async with conn.cursor() as cur:
        await cur.execute(METADATA_COLUMN_QUERY, (schema, table_name))
        row = await cur.fetchone()
        return row is not None


async def upsert_metadata(
    conn: psycopg.AsyncConnection,
    schema: str,
    table_name: str,
    id: int,
    pair_json: str,
) -> int:
    """Merge a single JSON pair into one record's ``metadata`` column.

    Args:
        conn: Database connection.
        schema: Database schema.
        table_name: Bare table name (already validated and access-checked).
        id: Primary-key value of the target record (bigint).
        pair_json: A JSON object string ``{"<key>": <value>}`` to merge.

    Returns:
        The number of rows affected (0 if no record matched the id, else 1).
    """
    statement = sql.SQL(_UPSERT_TEMPLATE).format(sql.Identifier(schema, table_name))

    start = time.monotonic()
    async with conn.cursor() as cur:
        await cur.execute(statement, (pair_json, id))
        rows_affected = cur.rowcount

    elapsed = time.monotonic() - start
    logger.debug(
        "upsert_metadata_sql",
        table=f"{schema}.{table_name}",
        sql=_UPSERT_TEMPLATE,
        rows_affected=rows_affected,
        elapsed_seconds=round(elapsed, 3),
    )
    return rows_affected
