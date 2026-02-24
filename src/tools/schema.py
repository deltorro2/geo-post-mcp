"""MCP tools for database schema discovery."""

from __future__ import annotations

import structlog

from src.services.access_control import is_table_allowed
from src.services.schema import describe_table as _describe_table
from src.services.schema import list_tables as _list_tables
from src.services.fieldmeaning import check_table_exists

logger = structlog.get_logger(__name__)


async def list_tables_tool(
    conn: object,
    schema: str,
    allowed_tables: list[str],
) -> list[dict[str, object]]:
    """List available tables in the database.

    Only returns tables that are in the allowed tables list.
    """
    logger.info("list_tables_tool_invoked")
    tables = await _list_tables(conn, schema, allowed_tables)  # type: ignore[arg-type]
    logger.info("list_tables_result", table_count=len(tables))
    return tables


async def describe_table_tool(
    table_name: str,
    conn: object,
    schema: str,
    allowed_tables: list[str],
) -> list[dict[str, object]]:
    """Describe columns of a table.

    Args:
        table_name: Table to describe.
        conn: Database connection.
        schema: Database schema.
        allowed_tables: Permitted table names.

    Returns:
        List of column details.
    """
    if not is_table_allowed(table_name, allowed_tables):
        raise ValueError(
            f"Access denied: table '{table_name}' is not in the allowed tables list."
        )

    exists = await check_table_exists(conn, schema, table_name)  # type: ignore[arg-type]
    if not exists:
        raise ValueError(f"Table '{table_name}' does not exist in schema '{schema}'.")

    logger.info("describe_table_tool_invoked", table_name=table_name)
    columns = await _describe_table(conn, schema, table_name)  # type: ignore[arg-type]
    logger.info("describe_table_result", table_name=table_name, column_count=len(columns))
    return columns
