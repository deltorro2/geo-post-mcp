"""MCP tool for querying column field meanings (comments)."""

from __future__ import annotations

import structlog

from src.models.fieldmeaning import FieldMeaningResponse
from src.services.access_control import is_table_allowed
from src.services.fieldmeaning import check_table_exists, get_field_meanings

logger = structlog.get_logger(__name__)


def validate_table_name(table_name: str) -> None:
    """Validate that a table name is bare (no schema qualifier).

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


async def fieldmeaning_tool(
    table_name: str,
    conn: object,
    schema: str,
    allowed_tables: list[str],
) -> dict[str, object]:
    """Get field meanings (column comments) for a table.

    Args:
        table_name: Bare table name (no schema qualifier).
        conn: Database connection.
        schema: Database schema.
        allowed_tables: Permitted table names.

    Returns:
        Dict with table, schema, and columns list.
    """
    validate_table_name(table_name)

    if not is_table_allowed(table_name, allowed_tables):
        raise ValueError(
            f"Access denied: table '{table_name}' is not in the allowed tables list."
        )

    exists = await check_table_exists(conn, schema, table_name)  # type: ignore[arg-type]
    if not exists:
        raise ValueError(f"Table '{table_name}' does not exist in schema '{schema}'.")

    logger.info("fieldmeaning_tool_invoked", table_name=table_name)

    entries = await get_field_meanings(conn, schema, table_name)  # type: ignore[arg-type]

    logger.info(
        "fieldmeaning_result",
        table_name=table_name,
        column_count=len(entries),
    )

    response = FieldMeaningResponse(
        table=table_name,
        schema_=schema,
        columns=entries,
    )
    return response.model_dump()
