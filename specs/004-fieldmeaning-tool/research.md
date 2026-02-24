# Research: Field Meaning Tool

**Branch**: `004-fieldmeaning-tool`
**Date**: 2026-02-23

## R1: PostgreSQL Column Comments Query

**Decision**: Use `pg_catalog.pg_description` joined with
`pg_catalog.pg_attribute` and `pg_catalog.pg_class` to
retrieve column comments. Use `information_schema.columns`
for data type and ordinal position.

**Rationale**: `pg_catalog` is the canonical source for
PostgreSQL object descriptions. The `col_description()`
built-in function is a simpler alternative but requires
per-column calls; a single JOIN query is more efficient
for retrieving all columns at once.

**Query pattern**:
```sql
SELECT
    c.column_name,
    c.data_type,
    c.ordinal_position,
    pgd.description
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st
    ON c.table_schema = st.schemaname
    AND c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid
    AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema = $1
    AND c.table_name = $2
ORDER BY c.ordinal_position;
```

**Alternatives considered**:
- `col_description(oid, int)` function: Simpler but requires
  N+1 calls or lateral join. Rejected for efficiency.
- `obj_description()`: Only works for table-level comments,
  not columns.

## R2: Table Existence Validation

**Decision**: Check table existence via
`information_schema.tables` before querying columns. This
provides a clear "table not found" error distinct from
"table has no columns."

**Rationale**: Separating existence check from column query
gives clear, specific error messages per FR-004.

**Alternatives considered**:
- Check via empty result set from column query: Ambiguous —
  cannot distinguish "table doesn't exist" from "table exists
  but has zero columns" (rare but possible for inherited
  tables).

## R3: Table Name Validation (Schema-Qualified Rejection)

**Decision**: Reject any table name containing a dot character
as a simple heuristic for schema-qualified names. The
`fieldmeaning` tool only accepts bare table names.

**Rationale**: Per clarification, bare names only. A dot in a
PostgreSQL identifier (outside double quotes) reliably
indicates schema qualification. This is a simple, safe check.

**Alternatives considered**:
- Parse and strip schema prefix: Rejected — would silently
  override the configured schema, violating the clarification.

## R4: Allowed Tables Enforcement

**Decision**: Check the table name against the allowed tables
list from settings before executing any database query. This
is the same pattern used by the query execution tool.

**Rationale**: Consistent access control across all tools
(FR-005). Checking before DB query avoids unnecessary
database round-trips for disallowed tables.

## R5: MCP Tool Registration with FastMCP

**Decision**: Use FastMCP's `@mcp.tool()` decorator to register
the `fieldmeaning` function. Input validated via Pydantic model
with a single `table_name: str` field. Output is a list of
`FieldMeaningEntry` Pydantic models serialized to the MCP
response.

**Rationale**: FastMCP is the project's chosen MCP SDK
(constitution). The decorator pattern provides automatic JSON
Schema generation for the MCP tool catalog (FR-007).

**Alternatives considered**:
- Manual tool registration: More boilerplate, no benefit over
  decorator approach.
