# Data Model: Field Meaning Tool

**Branch**: `004-fieldmeaning-tool`
**Date**: 2026-02-23

## Entities

### FieldMeaningRequest

The input to the `fieldmeaning` MCP tool.

| Field      | Type   | Required | Constraints                          |
|------------|--------|----------|--------------------------------------|
| table_name | string | yes      | Bare name only; must not contain `.` |

**Validation rules**:
- MUST NOT be empty.
- MUST NOT contain a dot (rejects schema-qualified names).
- MUST be in the allowed tables list from settings.
- Resolved against the schema configured in settings.

### FieldMeaningEntry

A single column's metadata in the tool response.

| Field            | Type        | Required | Description                              |
|------------------|-------------|----------|------------------------------------------|
| column_name      | string      | yes      | Column name from the database schema     |
| data_type        | string      | yes      | PostgreSQL data type (e.g., `integer`, `geometry`) |
| ordinal_position | integer     | yes      | Column position in the table (1-based)   |
| description      | string/null | yes      | Schema comment text, or null if none set |

**Ordering**: Results ordered by `ordinal_position` ascending.

### FieldMeaningResponse

The complete tool response.

| Field   | Type                   | Required | Description                    |
|---------|------------------------|----------|--------------------------------|
| table   | string                 | yes      | The queried table name         |
| schema  | string                 | yes      | The resolved schema name       |
| columns | list[FieldMeaningEntry] | yes      | All columns with their meanings |

## Relationships

```text
FieldMeaningRequest (1) ──queries──> (1) FieldMeaningResponse
FieldMeaningResponse (1) ──contains──> (N) FieldMeaningEntry
```

## State Transitions

None — this is a stateless read-only operation. No lifecycle
or state machine applies.
