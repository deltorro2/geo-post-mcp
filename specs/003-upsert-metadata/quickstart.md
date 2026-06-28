# Quickstart: Upsert Metadata Tool

## Prerequisites

- A configured `geo-post-mcp-settings.json` with `allowed_tables` including a table that has both an `id` column and a `metadata` (jsonb) column.
- `POSTGISMCPPASS` env var set for DB access.

## Try it (via an MCP client)

```python
# Add a new key (id is the bigint primary key, passed as an integer)
await client.call_tool("upsert_metadata", {
    "table_name": "parcels",
    "id": 42,
    "newkey": "source",
    "newvalue": "survey-2026",
})
# → {"table": "parcels", "id": 42, "key": "source", "status": "updated", "rows_affected": 1}

# Replace an existing key (other keys untouched)
await client.call_tool("upsert_metadata", {
    "table_name": "parcels", "id": 42, "newkey": "status", "newvalue": "published",
})

# Typed value: "2026" is stored as the number 2026
await client.call_tool("upsert_metadata", {
    "table_name": "parcels", "id": 42, "newkey": "year", "newvalue": "2026",
})
```

## Verify

```python
# metadata now contains the upserted pairs
await client.call_tool("query", {
    "sql": "SELECT id, metadata FROM parcels WHERE id = 42",
})
```

## Running the tests

```bash
cd src
pytest ../tests/unit/test_upsert_value_parsing.py ../tests/unit/test_upsert_service.py   # no DB needed
pytest ../tests/functional/test_upsert_tool.py                                            # needs live DB; skips if unavailable
ruff check .
```

## Test data note

Existing functional fixtures (`tests/functional/conftest.py`) build `test_parcels`/`test_buildings` with a `gid` primary key and **no `metadata` column**. The functional test for this feature must add a test table (e.g. `test_meta`) with an `id bigint PRIMARY KEY` and a `metadata jsonb` column, seeded with at least one row, and add it to `allowed_tables` (same pattern as `test_settings`). Cover: insert new key, replace existing key, typed value (`"2026"` → number), preserve other keys, non-existent id → `not_found`, disallowed table → error, table without `metadata` → error.

## Manual smoke check

After registering the tool, confirm the read-only guarantee is intact:

```python
# Still rejected — proves no general write path was opened (SC-005)
await client.call_tool("query", {"sql": "UPDATE parcels SET metadata = '{}'"})
# → ToolError: Only SELECT queries are permitted.
```
