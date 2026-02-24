"""MCP tool for executing SQL SELECT queries."""

from __future__ import annotations

import re

import structlog

from src.services.access_control import is_table_allowed
from src.services.query import execute_query
from src.services.sql_validator import validate_select_only

logger = structlog.get_logger(__name__)

# Simple regex to extract table names from SQL
TABLE_NAME_PATTERN = re.compile(
    r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)',
    re.IGNORECASE,
)

# Extract CTE aliases: WITH name AS, name AS
CTE_ALIAS_PATTERN = re.compile(
    r'\bWITH\s+(\w+)\s+AS\b|\b,\s*(\w+)\s+AS\b',
    re.IGNORECASE,
)


def extract_table_names(sql: str) -> list[str]:
    """Extract real table names referenced in a SQL statement.

    CTE aliases are excluded since they are not actual tables.
    """
    cte_matches = CTE_ALIAS_PATTERN.findall(sql)
    cte_aliases = {m[0] or m[1] for m in cte_matches if m[0] or m[1]}

    matches = TABLE_NAME_PATTERN.findall(sql)
    tables = []
    for match in matches:
        name = match[0] or match[1]
        if name and name not in cte_aliases:
            tables.append(name)
    return tables


async def query_tool(
    sql: str,
    conn: object,
    allowed_tables: list[str],
    row_limit: int = 1000,
) -> dict[str, object]:
    """Execute a SQL SELECT query.

    Args:
        sql: SQL SELECT statement to execute.
        conn: Database connection.
        allowed_tables: List of permitted table names.
        row_limit: Maximum rows to return.

    Returns:
        Dict with columns, rows, row_count, and truncated flag.
    """
    validate_select_only(sql)

    referenced_tables = extract_table_names(sql)
    for table in referenced_tables:
        if not is_table_allowed(table, allowed_tables):
            raise ValueError(
                f"Access denied: table '{table}' is not in the allowed tables list."
            )

    logger.info("query_tool_invoked", sql=sql[:200])

    result = await execute_query(conn, sql, row_limit)  # type: ignore[arg-type]
    response: dict[str, object] = {
        "columns": result.columns,
        "rows": result.rows,
        "row_count": result.row_count,
    }
    if result.truncated:
        response["truncated"] = True
        response["message"] = f"Results truncated to {row_limit} rows."
    return response
