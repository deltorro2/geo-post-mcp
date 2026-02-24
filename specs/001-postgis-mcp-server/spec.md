# Feature Specification: PostGIS MCP Server

**Feature Branch**: `001-postgis-mcp-server`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "I want to create MCP server which provides the interface to PostgreSQL server equipped with PostGIS. The server should allow the full specter of SELECT SQL requests, including requests of geo-data."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Standard SQL Queries (Priority: P1)

An AI assistant user connects to the MCP server and runs
standard SELECT queries against a PostgreSQL database. The user
can query any table, use JOINs, aggregations, subqueries,
CTEs, window functions, and all standard SQL SELECT features.
Results are returned in a structured format the assistant can
reason about.

**Why this priority**: SELECT queries are the core value
proposition. Without the ability to run arbitrary read queries,
the server has no purpose.

**Independent Test**: Can be fully tested by connecting to a
PostgreSQL database with sample tables and executing SELECT
queries of varying complexity. Delivers immediate value by
enabling AI assistants to explore and analyze relational data.

**Acceptance Scenarios**:

1. **Given** a PostgreSQL database with populated tables,
   **When** the user executes a simple SELECT query
   (e.g., `SELECT * FROM users LIMIT 10`),
   **Then** the system returns the matching rows with column
   names and typed values.

2. **Given** a PostgreSQL database with multiple related tables,
   **When** the user executes a complex query with JOINs,
   WHERE clauses, GROUP BY, and ORDER BY,
   **Then** the system returns the correct aggregated result set.

3. **Given** a valid SELECT query,
   **When** the query contains a syntax error,
   **Then** the system returns a clear error message indicating
   the nature and location of the error.

4. **Given** a connected database,
   **When** the user submits a non-SELECT statement
   (INSERT, UPDATE, DELETE, DROP, etc.),
   **Then** the system rejects the query and returns an error
   explaining that only SELECT operations are permitted.

---

### User Story 2 - Execute Geospatial Queries (Priority: P2)

An AI assistant user runs PostGIS-specific geospatial queries.
The user can call PostGIS functions such as ST_Distance,
ST_Contains, ST_Intersects, ST_Buffer, ST_AsGeoJSON, and
others. Geometry and geography results are returned in a
human-readable and machine-parseable format.

**Why this priority**: Geospatial querying is the differentiating
feature that justifies a PostGIS-specific server rather than a
generic SQL tool. It builds on the standard query capability
from User Story 1.

**Independent Test**: Can be tested by creating a table with a
geometry column, inserting sample spatial data, and running
PostGIS spatial queries. Delivers value by enabling AI
assistants to perform location-based analysis.

**Acceptance Scenarios**:

1. **Given** a table with a geometry column containing point data,
   **When** the user queries for points within a radius
   using ST_DWithin,
   **Then** the system returns the matching spatial records.

2. **Given** a table with polygon geometries,
   **When** the user runs a spatial join using ST_Contains
   or ST_Intersects,
   **Then** the system returns correctly matched geometry pairs.

3. **Given** a query that returns geometry values,
   **When** the results include geometry columns,
   **Then** geometry values are returned as GeoJSON strings
   for readability rather than raw WKB.

---

### User Story 3 - Discover Database Schema (Priority: P3)

An AI assistant user explores the database structure before
writing queries. The user can list available schemas, tables,
columns (with types), and discover which columns contain
spatial data and their spatial reference systems (SRID).

**Why this priority**: Schema discovery enables the AI assistant
to write correct queries without prior knowledge of the
database structure. It supports the query stories but is not
strictly required if the user already knows the schema.

**Independent Test**: Can be tested by connecting to a database
with multiple schemas, tables, and spatial columns, then
verifying that all structural metadata is accurately reported.

**Acceptance Scenarios**:

1. **Given** a connected PostgreSQL database,
   **When** the user requests a list of available tables,
   **Then** the system returns all tables grouped by schema
   with row count estimates.

2. **Given** a specific table name,
   **When** the user requests column details,
   **Then** the system returns each column's name, data type,
   nullability, and default value.

3. **Given** a database with PostGIS-enabled tables,
   **When** the user requests spatial column information,
   **Then** the system returns geometry type, SRID, and
   coordinate dimension for each spatial column.

---

### Edge Cases

- What happens when the database connection is lost mid-query?
  The system MUST return a connection error and attempt to
  reconnect on the next request.
- What happens when a query returns zero rows? The system MUST
  return an empty result set with column metadata intact.
- What happens when a query returns an extremely large result
  set? The system MUST enforce a configurable row limit and
  inform the user that results were truncated.
- What happens when the user references a table or column that
  does not exist? The system MUST return PostgreSQL's native
  error message clearly.
- What happens when PostGIS extension is not installed on the
  target database? The system MUST still function for standard
  SQL queries and return a clear error for PostGIS-specific
  function calls.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept arbitrary SELECT SQL statements
  and execute them against the connected PostgreSQL database.
- **FR-002**: System MUST reject any SQL statement that is not a
  SELECT query (INSERT, UPDATE, DELETE, CREATE, DROP, ALTER,
  TRUNCATE, and all other non-read operations).
- **FR-003**: System MUST support all PostGIS spatial functions
  available in the connected database version.
- **FR-004**: System MUST return geometry column values as
  GeoJSON strings by default.
- **FR-005**: System MUST return query results with column names,
  data types, and row data in a structured format.
- **FR-006**: System MUST enforce a configurable maximum row
  limit on query results (default: 1000 rows) and indicate
  when results are truncated.
- **FR-007**: System MUST provide schema introspection
  capabilities: list schemas, tables, columns, and spatial
  column metadata.
- **FR-008**: System MUST log all query executions with query
  text (parameters redacted), execution time, and row count.
- **FR-009**: System MUST handle database connection failures
  gracefully with clear error messages and automatic
  reconnection on subsequent requests.
- **FR-010**: System MUST expose its capabilities as MCP tools
  with complete JSON Schema definitions for all input
  parameters.
- **FR-011**: System MUST validate all user-provided SQL input
  before execution to confirm it is a SELECT statement.
- **FR-012**: System MUST support parameterized queries to
  prevent SQL injection when parameter values are provided
  separately from the query template.

### Key Entities

- **Database Connection**: Represents the connection to a
  PostgreSQL/PostGIS instance. Attributes: host, port,
  database name, credentials, connection pool settings.
- **Query Request**: A user-submitted SQL SELECT statement.
  Attributes: SQL text, optional parameters, optional row limit.
- **Query Result**: The structured response from a query.
  Attributes: column names, column types, row data, row count,
  truncation indicator, execution time.
- **Table Metadata**: Structural information about a database
  table. Attributes: schema name, table name, estimated row
  count, column list.
- **Column Metadata**: Structural information about a column.
  Attributes: column name, data type, nullability, default
  value, and for spatial columns: geometry type, SRID,
  coordinate dimension.

## Assumptions

- The PostgreSQL server is externally managed; this system does
  not provision or manage the database itself.
- Database connection credentials are provided via environment
  variables or configuration at server startup.
- The user (AI assistant) is trusted to run SELECT queries; no
  per-user access control is implemented beyond the
  SELECT-only restriction.
- PostGIS extension availability varies by database; the server
  gracefully degrades when PostGIS is not present.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can execute any valid SELECT query and
  receive structured results within 30 seconds for typical
  queries.
- **SC-002**: Users can execute PostGIS spatial queries and
  receive geometry results in GeoJSON format without additional
  conversion steps.
- **SC-003**: Users can discover the complete schema of an
  unfamiliar database (tables, columns, spatial metadata)
  using only the MCP tools provided.
- **SC-004**: 100% of non-SELECT SQL statements are rejected
  before reaching the database.
- **SC-005**: All query executions are logged with sufficient
  detail for debugging and auditing.
- **SC-006**: The system recovers from transient database
  connection failures without requiring a restart.
