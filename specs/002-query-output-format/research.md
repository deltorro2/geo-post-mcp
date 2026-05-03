# Research: Query Output Format

**Feature**: 002-query-output-format  
**Date**: 2026-04-30

## Research Task 1: Leaflet GeoJSON Compatibility

**Question**: What GeoJSON format does Leaflet require?

**Decision**: Standard RFC 7946 FeatureCollection with WGS84 coordinates. Leaflet's `L.geoJSON()` accepts FeatureCollection, individual Features, or arrays of Features. FeatureCollection is the recommended format for collections.

**Rationale**: 
- Leaflet expects EPSG:4326 (WGS84) — this is what PostGIS SRID 4326 already provides
- Null geometries are valid RFC 7946 and Leaflet handles them gracefully (not rendered)
- Extra properties at the FeatureCollection level (like `row_count`, `truncated`) are ignored by Leaflet but preserved for MCP clients
- Feature `properties` can contain arbitrary key-value pairs — Leaflet uses these for popups, styling, and filtering

**Alternatives considered**: None — RFC 7946 is the universal standard; no Leaflet-specific deviations needed.

## Research Task 2: Geometry Column Conversion Strategy

**Question**: How to convert PostGIS geometry values to GeoJSON geometry objects?

**Decision**: Wrap the user's SQL in a subquery and add `ST_AsGeoJSON(geom) AS __geojson` to convert the geometry column server-side. Use the `__geojson` column for Feature geometry and exclude the raw `geom` column from properties.

**Rationale**: 
- psycopg returns PostGIS geometry as WKB hex (e.g., `0101000020E6100000...`) which is not directly usable as GeoJSON
- `ST_AsGeoJSON()` is a PostGIS function that converts geometry to RFC 7946 GeoJSON string — reliable and handles all geometry types (Point, Polygon, LineString, MultiPolygon, etc.)
- Wrapping in a subquery (`SELECT *, ST_AsGeoJSON(geom) AS __geojson FROM ({sql}) AS __q`) avoids parsing or modifying the user's SQL
- The `__geojson` column returns a JSON string that can be parsed with `json.loads()` to get the geometry object

**Alternatives considered**:
- Client-side WKB parsing (e.g., shapely): Adds a heavy dependency; PostGIS already does this better
- Requiring users to include `ST_AsGeoJSON()` in their SQL: Bad UX; defeats the purpose of the `output_format` parameter
- Modifying the user's SQL to replace `geom` references: Fragile regex-based approach; breaks on complex queries

## Research Task 3: Geometry Column Detection

**Question**: How to detect the `geom` column in query results?

**Decision**: Check if the string `"geom"` exists in the result column names (case-sensitive match). Per the clarification session, geometry is identified by column name convention — the column must be named `geom`.

**Rationale**: Simple, deterministic, and aligned with the project's PostGIS schema conventions. The `geom` column name is standard in PostGIS-enabled databases.

**Alternatives considered**:
- Type-code inspection: `_is_geometry_type()` in `services/query.py` is currently stubbed (`return False`); PostGIS geometry OIDs are dynamically assigned and would require querying `pg_type`
- Pattern matching on values (WKB hex detection): Fragile and slow

## Research Task 4: Response Structure for GeoJSON

**Question**: Where should metadata (row_count, truncated) go in the GeoJSON response?

**Decision**: Include `row_count`, `truncated`, and `message` as top-level properties of the FeatureCollection object, alongside `type` and `features`. This is valid RFC 7946 (foreign members are allowed) and preserves MCP client compatibility.

**Rationale**: RFC 7946 Section 6.1 states: "Implementations MUST NOT extend the fixed set of types" but Section 6 allows "foreign members" (additional key-value pairs) at any level. Leaflet ignores unknown properties, so adding `row_count` and `truncated` to the FeatureCollection is safe.

**Alternatives considered**:
- Wrapping the FeatureCollection in an outer object: Breaks Leaflet compatibility (it expects FeatureCollection at the top level)
- Omitting metadata from GeoJSON responses: MCP clients lose truncation awareness
