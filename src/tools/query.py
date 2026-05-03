"""MCP tool for executing SQL SELECT queries."""

from __future__ import annotations

import json
import re
from typing import Any

from src.models.query import QueryResult
from src.services.access_control import is_table_allowed
from src.services.query import execute_query
from src.services.sql_validator import validate_select_only

# Simple regex to extract table names from SQL
TABLE_NAME_PATTERN = re.compile(
    r'\bFROM\s+((?:\w+\.)\w+|\w+)|\bJOIN\s+((?:\w+\.)\w+|\w+)',
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
    Handles schema-qualified names like schema.table → returns 'table'.
    """
    cte_matches = CTE_ALIAS_PATTERN.findall(sql)
    cte_aliases = {m[0] or m[1] for m in cte_matches if m[0] or m[1]}

    matches = TABLE_NAME_PATTERN.findall(sql)
    tables = []
    for match in matches:
        name = match[0] or match[1]
        if name and name not in cte_aliases:
            # Strip schema qualifier: "remez1.polygons" → "polygons"
            table_only = name.split('.')[-1]
            tables.append(table_only)
    return tables

VALID_OUTPUT_FORMATS = ("text", "geojson")


async def query_tool(
    sql: str,
    conn: object,
    schema: str,
    allowed_tables: list[str],
    row_limit: int = 1000,
    output_format: str = "text",
) -> dict[str, object]:
    """Execute a SQL SELECT query.

    Args:
        sql: SQL SELECT statement to execute.
        conn: Database connection.
        schema: Database schema.
        allowed_tables: List of permitted table names.
        row_limit: Maximum rows to return.
        output_format: "text" for tabular data, "geojson" for FeatureCollection.

    Returns:
        Dict with columns, rows, row_count, and truncated flag (text),
        or a GeoJSON FeatureCollection dict (geojson).
    """
    if output_format not in VALID_OUTPUT_FORMATS:
        raise ValueError(
            f"Invalid output_format '{output_format}'. "
            f"Valid options: {', '.join(repr(f) for f in VALID_OUTPUT_FORMATS)}."
        )

    validate_select_only(sql)

    referenced_tables = extract_table_names(sql)
    for table in referenced_tables:
        if not is_table_allowed(table, schema, allowed_tables):
            raise ValueError(
                f"Access denied: table '{table}' is not in the allowed tables list."
            )

    # When geojson requested, wrap SQL to convert geom via ST_AsGeoJSON.
    # Use __geom_geojson alias to avoid duplicate column name with *.
    exec_sql = sql
    if output_format == "geojson":
        exec_sql = (
            f"SELECT *, ST_AsGeoJSON(geom) AS __geom_geojson"
            f" FROM ({sql}) AS __inner"
        )

    try:
        result = await execute_query(conn, exec_sql, row_limit)  # type: ignore[arg-type]
    except Exception as exc:
        # If the wrapping SQL fails because geom column doesn't exist,
        # provide a user-friendly error message.
        if output_format == "geojson" and "geom" in str(exc).lower():
            raise ValueError(
                "GeoJSON output requires a column named 'geom' in the query results."
            ) from exc
        raise

    if output_format == "geojson":
        return _to_geojson_feature_collection(result, row_limit)

    response: dict[str, object] = {
        "columns": result.columns,
        "rows": result.rows,
        "row_count": result.row_count,
    }
    if result.truncated:
        response["truncated"] = True
        response["message"] = f"Results truncated to {row_limit} rows."
    return response


def _to_geojson_feature_collection(
    result: QueryResult, row_limit: int
) -> dict[str, Any]:
    """Convert a QueryResult to a GeoJSON FeatureCollection.

    The `geom` column is used as Feature geometry (expected to be a
    GeoJSON string from ST_AsGeoJSON). All other columns become
    Feature properties.

    Args:
        result: Query result with columns and rows.
        row_limit: Row limit used for truncation message.

    Returns:
        GeoJSON FeatureCollection dict compatible with Leaflet.

    Raises:
        ValueError: If no `geom` column is found in the results.
    """
    # The SQL wrapper adds __geom_geojson from ST_AsGeoJSON(geom).
    # If __geom_geojson is missing, the user's query had no geom column.
    if "__geom_geojson" not in result.columns:
        raise ValueError(
            "GeoJSON output requires a column named 'geom' in the query results."
        )

    geojson_idx = result.columns.index("__geom_geojson")
    # Exclude both the raw geom and __geom_geojson from properties
    skip = {"geom", "__geom_geojson"}
    prop_indices = [i for i in range(len(result.columns)) if result.columns[i] not in skip]
    prop_names = [result.columns[i] for i in prop_indices]

    features: list[dict[str, Any]] = []
    for row in result.rows:
        geom_val = row[geojson_idx]
        if geom_val is not None:
            geometry = json.loads(geom_val) if isinstance(geom_val, str) else geom_val
        else:
            geometry = None

        properties = {prop_names[j]: row[prop_indices[j]] for j in range(len(prop_names))}
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    fc: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": features,
        "row_count": result.row_count,
    }
    if result.truncated:
        fc["truncated"] = True
        fc["message"] = f"Results truncated to {row_limit} rows."
    return fc
