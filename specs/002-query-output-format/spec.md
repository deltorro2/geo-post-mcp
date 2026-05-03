# Feature Specification: Query Output Format

**Feature Branch**: `002-query-output-format`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: User description: "Extended query tool with additional parameter which defines the output format. Possible formats text/geojson. Provide clear explanation about both and emphasize that geojson is recommended to draw vector objects graphically in UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - GeoJSON Output for Map Visualization (Priority: P1)

As an MCP client building a map-based interface, I want to request query results in GeoJSON format so I can render spatial data as vector objects on a map without any post-processing.

**Why this priority**: GeoJSON output is the primary motivation for this feature — enabling spatial visualization is the core value that doesn't exist today.

**Independent Test**: Can be tested by executing a spatial query with `output_format` set to `"geojson"` and verifying the response is a valid GeoJSON FeatureCollection with geometry and properties.

**Acceptance Scenarios**:

1. **Given** a query that returns rows with a geometry column, **When** the client calls the query tool with `output_format="geojson"`, **Then** the response is a GeoJSON FeatureCollection where each row becomes a Feature with its geometry and non-geometry columns as properties.
2. **Given** a query that returns rows with a geometry column, **When** the client calls the query tool with `output_format="geojson"`, **Then** geometry values are valid GeoJSON geometry objects (Point, Polygon, LineString, etc.) with coordinates.
3. **Given** a query that returns no geometry column, **When** the client calls the query tool with `output_format="geojson"`, **Then** the system returns an error indicating that GeoJSON output requires at least one geometry column in the query results.

---

### User Story 2 - Text Output as Default (Priority: P2)

As an MCP client that needs tabular data for textual answers, I want the existing text/tabular output format to remain the default so that all current behavior is preserved without any changes needed by existing clients.

**Why this priority**: Backward compatibility ensures existing clients continue to work without modification.

**Independent Test**: Can be tested by calling the query tool without specifying `output_format` (or with `output_format="text"`) and verifying the response matches the current tabular format (columns, rows, row_count).

**Acceptance Scenarios**:

1. **Given** any valid SELECT query, **When** the client calls the query tool without specifying `output_format`, **Then** the response is in the existing tabular format with `columns`, `rows`, and `row_count` fields.
2. **Given** any valid SELECT query, **When** the client calls the query tool with `output_format="text"`, **Then** the response is identical to calling without the parameter.

---

### User Story 3 - Clear Tool Description for MCP Clients (Priority: P3)

As an MCP client (typically an AI assistant), I want the query tool's description to clearly explain both output formats and recommend GeoJSON for spatial visualization, so I can make the right choice based on the user's intent.

**Why this priority**: Good tool documentation helps AI clients make intelligent format choices without user intervention.

**Independent Test**: Can be tested by listing tools via MCP and verifying the query tool description mentions both formats and recommends GeoJSON for map/visual rendering.

**Acceptance Scenarios**:

1. **Given** an MCP client listing available tools, **When** it reads the query tool description, **Then** the description explains that `output_format` accepts `"text"` (default, tabular data for textual answers) and `"geojson"` (GeoJSON FeatureCollection, recommended for drawing vector objects graphically in UI).
2. **Given** an MCP client reading the query tool description, **When** it sees the `output_format` parameter, **Then** the parameter description clearly states that `"geojson"` is recommended when the intent is to render spatial data on a map.

---

### Edge Cases

- What happens when `output_format` is set to an unsupported value (e.g., `"csv"`)? The system should return an error listing the valid options (`"text"`, `"geojson"`).
- What happens when `output_format="geojson"` is used with a query that has multiple columns? Only the column named `geom` is used as the Feature geometry; all other columns become properties.
- What happens when `output_format="geojson"` is used and the query result contains null geometry values? Those rows should still appear as Features with `null` geometry.
- What happens when `output_format="geojson"` is used with row_limit truncation? The truncation indicator should be included in the GeoJSON response metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The query tool MUST accept an `output_format` parameter with two valid values: `"text"` and `"geojson"`.
- **FR-002**: The `output_format` parameter MUST default to `"text"` when not specified, preserving full backward compatibility with existing clients.
- **FR-003**: When `output_format="text"`, the response MUST match the existing tabular format (`columns`, `rows`, `row_count`, and optional `truncated`/`message` fields).
- **FR-004**: When `output_format="geojson"`, the response MUST be a GeoJSON FeatureCollection where each result row is a Feature with geometry extracted from the column named `geom` and all other columns as properties.
- **FR-005**: When `output_format="geojson"` and the query results contain no column named `geom`, the system MUST return an error indicating that GeoJSON output requires a column named `geom`.
- **FR-006**: When `output_format` is set to an unsupported value, the system MUST return an error listing the valid options.
- **FR-007**: The query tool description (visible to MCP clients) MUST explain both formats and recommend GeoJSON when the intent is to draw vector objects graphically in a UI.
- **FR-008**: GeoJSON output MUST include the `row_count` and, if applicable, `truncated` and `message` fields alongside the FeatureCollection to preserve result metadata.

### Key Entities

- **FeatureCollection**: The top-level GeoJSON response object containing an array of Features and result metadata (row count, truncation status).
- **Feature**: A single result row represented as a GeoJSON Feature with a `geometry` field (from the `geom` column) and a `properties` field (all other columns as key-value pairs).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Queries with spatial data can be returned in GeoJSON format that is directly renderable by any standard map library without transformation.
- **SC-002**: Existing clients calling the query tool without the new parameter receive identical responses to the current behavior (zero breaking changes).
- **SC-003**: An MCP client reading the tool description can determine which format to use based solely on the description text, without external documentation.
- **SC-004**: 100% of valid GeoJSON responses pass GeoJSON specification validation (RFC 7946).

## Clarifications

### Session 2026-04-30

- Q: How should the system identify which column contains geometry data? → A: By column name convention — the column must be named `geom`.

## Assumptions

- The existing query tool already handles geometry columns via PostGIS and returns them as text. The GeoJSON format will convert these to proper GeoJSON geometry objects.
- The `ST_AsGeoJSON` PostGIS function is available and will be used internally to convert geometry values.
- Geometry is identified by the column name `geom`. Only one geometry column is expected per query; all other columns become Feature properties.
- The `output_format` parameter is a simple string, not an enum, to keep the MCP tool schema simple and client-friendly.
