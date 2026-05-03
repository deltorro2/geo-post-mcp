# Implementation Plan: Query Output Format

**Branch**: `002-query-output-format` | **Date**: 2026-04-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-query-output-format/spec.md`
**Additional context**: GeoJSON output must be compatible with Leaflet (JavaScript map library) — standard RFC 7946 FeatureCollection in WGS84 (EPSG:4326).

## Summary

Add an `output_format` parameter to the query tool with two modes: `"text"` (default, existing tabular format) and `"geojson"` (RFC 7946 FeatureCollection compatible with Leaflet's `L.geoJSON()`). The geometry column is identified by name (`geom`) and converted to GeoJSON geometry objects using PostGIS `ST_AsGeoJSON()`. All other columns become Feature properties. The tool description is updated to explain both formats and recommend GeoJSON for map visualization.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastMCP (MCP Python SDK), psycopg, structlog  
**Storage**: PostgreSQL with PostGIS (EPSG:4326 / WGS84)  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux server (Docker container)  
**Project Type**: MCP server (stdio transport)  
**Performance Goals**: N/A (output formatting, no throughput changes)  
**Constraints**: GeoJSON must be valid RFC 7946 and directly usable by Leaflet's `L.geoJSON()`; no new dependencies  
**Scale/Scope**: 1 MCP tool modified, ~4 source files changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | Adding an optional parameter preserves JSON Schema compliance; tool still returns dict |
| II. Type Safety | PASS | `output_format` typed as `str` with validation; GeoJSON response is a typed dict |
| III. Syntactic Simplicity | PASS | Single conversion function; no new abstractions beyond `_to_geojson_feature_collection()` |
| IV. Log Coverage | PASS | Existing middleware logs tool name + parameters; `output_format` included automatically |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-query-output-format/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── server.py               # MODIFY: add output_format param to query(), update docstring
├── tools/
│   └── query.py            # MODIFY: add output_format param, add format validation, add GeoJSON conversion logic
├── services/
│   └── query.py            # KEEP: no changes (returns QueryResult as before)
└── models/
    └── query.py            # KEEP: QueryResult unchanged

tests/
├── unit/
│   └── test_query_geojson.py    # NEW: unit tests for GeoJSON conversion
└── functional/
    └── test_geo_query_tool.py   # MODIFY: add GeoJSON output format tests
```

**Structure Decision**: Existing `src/` layout preserved. GeoJSON conversion logic lives in `src/tools/query.py` alongside the existing `query_tool()` function since it's output formatting, not a service-level concern.

## Implementation Approach

### Strategy: Post-Query Conversion

The GeoJSON conversion happens after the existing query execution, transforming the `QueryResult` (columns + rows) into a FeatureCollection. This avoids modifying the SQL or the query service layer.

**Flow**:
1. `query()` in `server.py` passes `output_format` to `query_tool()`
2. `query_tool()` validates `output_format` (must be `"text"` or `"geojson"`)
3. `query_tool()` calls `execute_query()` as before, getting `QueryResult`
4. If `output_format="text"`: return existing dict format (no change)
5. If `output_format="geojson"`: find `geom` column index, convert each row to a Feature, wrap in FeatureCollection

### GeoJSON Conversion Details

For each row in the result:
1. Find the index of the `geom` column in `columns`
2. The `geom` value is a WKB hex string from PostGIS — convert it using `ST_AsGeoJSON()` by wrapping the original SQL: the simplest approach is to parse the geometry value. However, since psycopg returns geometry as WKB hex, we need to convert. The cleanest approach: modify the SQL to add `ST_AsGeoJSON(geom)` when `output_format="geojson"`, or parse the WKB hex client-side.

**Decision**: Modify the SQL by replacing `geom` references in the SELECT with `ST_AsGeoJSON(geom)` is fragile. Instead, run a second lightweight query to convert geometry values, or better yet: since the `geom` column already comes through as a raw value, we'll use PostGIS `ST_AsGeoJSON()` by wrapping the user's query in a CTE and selecting with geometry conversion.

**Revised approach**: Wrap the user's SQL in a subquery when `output_format="geojson"`:
```sql
SELECT *, ST_AsGeoJSON(geom) AS __geojson FROM ({user_sql}) AS __q
```
This ensures `geom` is converted to GeoJSON regardless of how the user wrote the query. The `__geojson` column is used for the Feature geometry, the original `geom` column is excluded from properties.

### Leaflet Compatibility

Leaflet's `L.geoJSON()` expects standard RFC 7946:
- **CRS**: WGS84 (EPSG:4326) — PostGIS data in SRID 4326 already satisfies this
- **Structure**: `{"type": "FeatureCollection", "features": [...]}`
- **Features**: `{"type": "Feature", "geometry": {...}, "properties": {...}}`
- **Null geometry**: Leaflet handles gracefully (feature not rendered)
- **Extra fields**: Allowed at FeatureCollection level for metadata (`row_count`, `truncated`)

### Response Structure

**GeoJSON response** (`output_format="geojson"`):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [34.05, -118.25]},
      "properties": {"gid": 1, "name": "Park A", "area_sqm": 5000.0}
    }
  ],
  "row_count": 1,
  "truncated": false
}
```

**Text response** (`output_format="text"`, unchanged):
```json
{
  "columns": ["gid", "name", "geom"],
  "rows": [[1, "Park A", "0101000020E6..."]],
  "row_count": 1
}
```
