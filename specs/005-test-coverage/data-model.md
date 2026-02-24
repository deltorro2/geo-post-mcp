# Data Model: Test Coverage

**Branch**: `005-test-coverage`
**Date**: 2026-02-23

## Entities

This feature produces tests, not data models. The entities
below describe the test fixtures and test database objects
used by the test suite.

### Test Database Fixtures

Objects created in the test database for functional tests.

#### Test Table: `test_parcels`

| Column    | Type             | Comment                        |
|-----------|------------------|--------------------------------|
| gid       | integer          | "Unique parcel identifier"     |
| name      | varchar(100)     | "Human-readable parcel name"   |
| area_sqm  | double precision | (no comment)                   |
| geom      | geometry(Polygon, 4326) | "Parcel boundary polygon" |

Purpose: Tests SQL query tool, geospatial queries, fieldmeaning
tool (mix of commented and uncommented columns), and schema
discovery.

#### Test Table: `test_buildings`

| Column    | Type             | Comment                      |
|-----------|------------------|------------------------------|
| bid       | integer          | "Building identifier"        |
| parcel_id | integer          | "Reference to parent parcel" |
| height_m  | double precision | "Building height in meters"  |
| location  | geometry(Point, 4326) | "Building centroid"     |

Purpose: Tests JOINs between tables, spatial queries across
tables, and multi-table access control.

#### Test Table: `test_restricted`

| Column | Type    | Comment           |
|--------|---------|-------------------|
| id     | integer | "Restricted data" |
| secret | text    | "Sensitive value" |

Purpose: NOT included in allowed_tables. Used to verify access
control rejects queries and fieldmeaning requests for this
table.

### Test Settings File

A `geo-post-mcp-settings.json` used by functional tests:

```json
{
  "host": "<test_db_host>",
  "port": 5432,
  "user": "<test_db_user>",
  "schema": "public",
  "allowed_tables": ["test_parcels", "test_buildings"]
}
```

Note: `test_restricted` is intentionally excluded from
`allowed_tables` to test access denial.

### Pytest Markers

| Marker       | Scope      | Description                        |
|--------------|------------|------------------------------------|
| unit         | per-test   | No external dependencies required  |
| functional   | per-test   | Requires PostgreSQL with PostGIS   |

## Relationships

```text
test_parcels (1) ──referenced by──> (N) test_buildings (via parcel_id)
test_restricted ──not in allowed_tables──> access denied
```

## State Transitions

No state transitions — test fixtures are created before tests
and rolled back after each test via transaction rollback.
