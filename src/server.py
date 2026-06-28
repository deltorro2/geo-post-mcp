"""MCP server entrypoint for geo-post-mcp."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import psycopg
import structlog
from fastmcp import FastMCP

from src.config.logging import setup_logging
from src.config.settings import Settings, load_settings
from src.middleware.logging import ToolLoggingMiddleware
from src.services.database import create_connection
from src.tools.fieldmeaning import fieldmeaning_tool
from src.tools.query import query_tool
from src.tools.schema import describe_table_tool, list_tables_tool
from src.tools.upsert import upsert_metadata_tool


def _parse_settings_path() -> Path | None:
    """Parse --sett CLI argument to get settings file path."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--sett", type=Path, default=None, help="Path to settings file")
    args, _ = parser.parse_known_args()
    result: Path | None = args.sett
    return result


_cli_settings_path: Path | None = _parse_settings_path()
_initial_settings: Settings = load_settings(_cli_settings_path)

setup_logging(
    level=logging.getLevelNamesMapping()[_initial_settings.log_level.upper()],
    log_file=_initial_settings.log_file,
)
logger = structlog.get_logger(__name__)
logger.info("------------------------------------SERVER STARTED--------------------------------")
if _cli_settings_path is not None:
    logger.info("settings_path_override", path=str(_cli_settings_path.resolve()))

mcp = FastMCP("geo-post-mcp")
mcp.add_middleware(ToolLoggingMiddleware())

# Module-level state set during startup
_settings: Settings | None = _initial_settings
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
        _settings = load_settings(_cli_settings_path)
    if _conn is None or _conn.closed:
        _conn = await create_connection(_settings)
    return _conn


@mcp.tool()
async def query(
    sql: str, row_limit: int = 1000, output_format: str = "text"
) -> dict[str, object]:
    """Execute a SQL SELECT query against the database.

    Only SELECT queries are permitted. Results are truncated at row_limit.

    Args:
        sql: SQL SELECT statement to execute.
        row_limit: Maximum number of rows to return (default 1000).
        output_format: Response format. "text" (default) returns tabular data
            with columns, rows, and row_count — best for textual answers.
            "geojson" returns a GeoJSON FeatureCollection (RFC 7946) where
            each row becomes a Feature with geometry from the 'geom' column
            and all other columns as properties. GeoJSON is recommended for
            drawing vector objects graphically in UI (e.g. Leaflet maps).
            The query must include a column named 'geom' for GeoJSON output.
    """
    conn = await _get_connection()
    assert _settings is not None
    return await query_tool(
        sql, conn, _settings.schema_, _settings.allowed_tables, row_limit, output_format
    )


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


@mcp.tool()
async def upsert_metadata(
    table_name: str, id: int, newkey: str, newvalue: str
) -> dict[str, object]:
    """Insert or replace a single key/value pair in a record's metadata column.

    The record is located by its 'id' (the table's bigint primary key). If
    'newkey' already exists, its value is replaced; otherwise it is added. All
    other keys are preserved. 'newvalue' is stored as its native JSON type when
    it is valid JSON (e.g. 42, true, [1,2]), otherwise as a string.

    This is the only tool permitted to write data, and it writes only to the
    'metadata' column. All other tools remain read-only.

    Args:
        table_name: Bare table name (no schema qualifier).
        id: Primary-key value of the target record.
        newkey: Metadata key to insert or replace.
        newvalue: Value to store (auto-detected as JSON or stored as a string).
    """
    conn = await _get_connection()
    assert _settings is not None
    return await upsert_metadata_tool(
        table_name, id, newkey, newvalue, conn, _settings.schema_, _settings.allowed_tables
    )


if __name__ == "__main__":
    mcp.run()
