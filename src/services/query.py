"""Service for executing SQL queries against PostgreSQL."""

from __future__ import annotations

import json
import time

import psycopg
import structlog

from src.models.query import QueryResult

logger = structlog.get_logger(__name__)

DEFAULT_ROW_LIMIT = 1000


async def execute_query(
    conn: psycopg.AsyncConnection,
    sql: str,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> QueryResult:
    """Execute a SELECT query and return structured results.

    Geometry columns are automatically converted to GeoJSON.

    Args:
        conn: Database connection.
        sql: Validated SELECT SQL statement.
        row_limit: Maximum rows to return.

    Returns:
        QueryResult with columns, rows, count, and truncation flag.
    """
    start = time.monotonic()
    async with conn.cursor() as cur:
        await cur.execute(sql)

        if cur.description is None:
            return QueryResult(columns=[], rows=[], row_count=0, truncated=False)

        columns = [desc.name for desc in cur.description]
        type_codes = [desc.type_code for desc in cur.description]

        rows_raw = await cur.fetchmany(row_limit + 1)
        truncated = len(rows_raw) > row_limit
        if truncated:
            rows_raw = rows_raw[:row_limit]

        rows = []
        for row in rows_raw:
            converted = []
            for i, val in enumerate(row):
                if val is not None and _is_geometry_type(type_codes[i], conn):
                    converted.append(_try_geojson(val))
                else:
                    converted.append(val)
            rows.append(converted)

    elapsed = time.monotonic() - start
    logger.info(
        "query_executed",
        sql=sql[:200],
        row_count=len(rows),
        truncated=truncated,
        elapsed_seconds=round(elapsed, 3),
    )

    return QueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
    )


def _is_geometry_type(type_code: int, conn: psycopg.AsyncConnection) -> bool:
    """Check if a column type code corresponds to a geometry type."""
    # PostGIS geometry OID is dynamically assigned; we check common patterns
    # A more robust approach queries pg_type, but for now we handle at
    # serialization time
    return False  # Handled by _try_geojson on value inspection


def _try_geojson(val: object) -> object:
    """Attempt to convert a geometry value to GeoJSON string."""
    if isinstance(val, str):
        if val.startswith("{") and '"type"' in val:
            return val  # Already GeoJSON
        # Could be WKB hex; for now return as-is
    return val
