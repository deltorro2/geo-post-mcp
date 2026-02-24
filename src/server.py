"""MCP server entrypoint for geo-post-mcp."""

from __future__ import annotations

import psycopg
import structlog
from fastmcp import FastMCP

from src.config.logging import setup_logging
from src.config.settings import Settings, load_settings
from src.services.database import create_connection
from src.tools.fieldmeaning import fieldmeaning_tool
from src.tools.query import query_tool
from src.tools.schema import describe_table_tool, list_tables_tool

setup_logging()
logger = structlog.get_logger(__name__)

mcp = FastMCP("geo-post-mcp")

# Module-level state set during startup
_settings: Settings | None = None
_conn: psycopg.AsyncConnection | None = None


def configure(settings: Settings, conn: psycopg.AsyncConnection | None = None) -> None:
    """Inject settings and optional connection (used by tests)."""
    global _settings, _conn
    _settings = settings
    _conn = conn


async def _get_connection() -> psycopg.AsyncConnection:
    """Get or create the database connection."""
    global _conn, _settings
    if _settings is None:
        _settings = load_settings()
    if _conn is None or _conn.closed:
        _conn = await create_connection(_settings)
    return _conn


@mcp.tool()
async def query(sql: str, row_limit: int = 1000) -> dict[str, object]:
    """Execute a SQL SELECT query against the database.

    Only SELECT queries are permitted. Results are returned with
    column names, typed values, and a row count. Geometry columns
    are returned as GeoJSON. Results are truncated at row_limit.

    Args:
        sql: SQL SELECT statement to execute.
        row_limit: Maximum number of rows to return (default 1000).
    """
    conn = await _get_connection()
    assert _settings is not None
    return await query_tool(sql, conn, _settings.allowed_tables, row_limit)


@mcp.tool()
async def list_tables() -> list[dict[str, object]]:
    """List all available tables in the database.

    Returns table names, schemas, and estimated row counts.
    Only tables in the allowed list are returned.
    """
    conn = await _get_connection()
    assert _settings is not None
    return await list_tables_tool(conn, _settings.schema_, _settings.allowed_tables)


@mcp.tool()
async def describe_table(table_name: str) -> list[dict[str, object]]:
    """Describe the columns of a database table.

    Returns column names, data types, nullability, defaults,
    and spatial metadata for geometry columns.

    Args:
        table_name: Name of the table to describe.
    """
    conn = await _get_connection()
    assert _settings is not None
    return await describe_table_tool(
        table_name, conn, _settings.schema_, _settings.allowed_tables
    )


@mcp.tool()
async def fieldmeaning(table_name: str) -> dict[str, object]:
    """Get field meanings (column comments) for a database table.

    Returns each column's name, data type, ordinal position,
    and description (from schema comments). Only bare table
    names are accepted (no schema qualifier).

    Args:
        table_name: Bare table name (no schema qualifier like 'public.tablename').
    """
    conn = await _get_connection()
    assert _settings is not None
    return await fieldmeaning_tool(
        table_name, conn, _settings.schema_, _settings.allowed_tables
    )
