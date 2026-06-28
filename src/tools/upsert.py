"""MCP tool for upserting a key/value pair into a record's metadata column."""

from __future__ import annotations

import json
import time

import structlog

from src.models.upsert import UpsertResult
from src.services.access_control import is_table_allowed
from src.services.fieldmeaning import check_table_exists
from src.services.upsert import has_metadata_column, upsert_metadata

logger = structlog.get_logger(__name__)

_VALUE_LOG_MAX_LEN = 200


def parse_value(newvalue: str) -> tuple[object, str]:
    """Auto-detect the JSON type of ``newvalue``.

    If ``newvalue`` is valid JSON it is returned as its native typed value;
    otherwise it is treated as a plain string.

    Args:
        newvalue: The raw value supplied to the tool.

    Returns:
        A tuple of (parsed value, value-type label). The label is one of
        ``number``, ``boolean``, ``null``, ``array``, ``object``, ``string``.
    """
    try:
        parsed = json.loads(newvalue)
    except json.JSONDecodeError:
        return newvalue, "string"
    return parsed, _json_type(parsed)


def _json_type(value: object) -> str:
    """Return the JSON-type label for a parsed value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def validate_table_name(table_name: str) -> None:
    """Validate that a table name is non-empty and bare (no schema qualifier).

    Raises:
        ValueError: If table name is empty or contains a dot.
    """
    if not table_name:
        raise ValueError("Table name must not be empty.")
    if "." in table_name:
        raise ValueError(
            f"Schema-qualified names are not supported. "
            f"Use bare table name instead of '{table_name}'."
        )


async def upsert_metadata_tool(
    table_name: str,
    id: int,
    newkey: str,
    newvalue: str,
    conn: object,
    schema: str,
    allowed_tables: list[str],
) -> dict[str, object]:
    """Insert or replace one key/value pair in a record's metadata column.

    Args:
        table_name: Bare table name (no schema qualifier).
        id: Primary-key value of the target record (bigint).
        newkey: Key to insert or replace.
        newvalue: Value to store; auto-detected as JSON when valid, else string.
        conn: Database connection.
        schema: Database schema.
        allowed_tables: Permitted schema-qualified table names.

    Returns:
        Serialized UpsertResult with table, id, key, status, and rows_affected.
    """
    validate_table_name(table_name)
    if not newkey:
        raise ValueError("newkey must not be empty.")

    value, value_type = parse_value(newvalue)
    logger.info(
        "upsert_metadata_requested",
        table=table_name,
        id=id,
        newkey=newkey,
        newvalue=newvalue[:_VALUE_LOG_MAX_LEN],
        value_type=value_type,
    )

    if not is_table_allowed(table_name, schema, allowed_tables):
        raise ValueError(
            f"Access denied: table '{table_name}' is not in the allowed tables list."
        )
    if not await check_table_exists(conn, schema, table_name):  # type: ignore[arg-type]
        raise ValueError(f"Table '{table_name}' does not exist in schema '{schema}'.")
    if not await has_metadata_column(conn, schema, table_name):  # type: ignore[arg-type]
        raise ValueError(
            f"Table '{table_name}' is not eligible for metadata upsert "
            f"(no 'metadata' column)."
        )

    pair_json = json.dumps({newkey: value})
    start = time.perf_counter()
    rows_affected = await upsert_metadata(conn, schema, table_name, id, pair_json)  # type: ignore[arg-type]
    elapsed = time.perf_counter() - start

    status = "updated" if rows_affected > 0 else "not_found"
    logger.info(
        "upsert_metadata_completed",
        table=table_name,
        id=id,
        newkey=newkey,
        status=status,
        rows_affected=rows_affected,
        elapsed_seconds=round(elapsed, 3),
    )

    result = UpsertResult(
        table=table_name,
        id=id,
        key=newkey,
        status=status,
        rows_affected=rows_affected,
    )
    return result.model_dump()
