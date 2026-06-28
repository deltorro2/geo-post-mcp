# Tool Contract: `upsert_metadata`

MCP tool registered in `src/server.py` via `@mcp.tool()`.

## Signature

```python
async def upsert_metadata(
    table_name: str,
    id: int,
    newkey: str,
    newvalue: str,
) -> dict[str, object]:
    ...
```

The typed signature produces the MCP input JSON Schema (Constitution Principle I). `table_name`, `newkey`, and `newvalue` are required strings; `id` is a required integer, bound directly against the table's `bigint` primary-key `id` column (no string coercion).

## Description (tool docstring intent)

> Insert or replace a single key/value pair in the `metadata` (JSON) column of one record. The record is located by its `id` (the table's bigint primary key). If `newkey` already exists, its value is replaced; otherwise it is added. All other keys are preserved. `newvalue` is stored as its native JSON type when it is valid JSON (e.g. `42`, `true`, `[1,2]`), otherwise as a string. This is the only tool permitted to write data, and it writes only to the `metadata` column.

## Behavior

1. Validate `table_name` (non-empty, bare) and `newkey` (non-empty).
2. Deny if `table_name` is not in the allowed-tables list.
3. Error if the table does not exist, or lacks a `metadata` column (the `id` bigint PK is guaranteed by convention).
4. Detect the JSON type of `newvalue`.
5. Execute one atomic UPDATE merging `{newkey: value}` into `metadata`.
6. Return the result; log parameters and outcome at INFO.

## Success response

```json
{
  "table": "parcels",
  "id": 42,
  "key": "source",
  "status": "updated",
  "rows_affected": 1
}
```

## No-match response (record id not found — no data changed)

```json
{
  "table": "parcels",
  "id": 999,
  "key": "source",
  "status": "not_found",
  "rows_affected": 0
}
```

## Error responses (raised as MCP `ToolError`, no data changed)

| Trigger | Message (substring) |
|---------|---------------------|
| Empty table name | `Table name must not be empty` |
| Schema-qualified table name | `Schema-qualified names are not supported` |
| Empty key | `newkey must not be empty` |
| Table not allowed | `Access denied: table '<t>' is not in the allowed tables list` |
| Table missing | `Table '<t>' does not exist in schema '<s>'` |
| Table ineligible (no `metadata` column) | `Table '<t>' is not eligible for metadata upsert` |

## Logging contract (Constitution IV + user directive)

- **INFO** `upsert_metadata_requested`: `table`, `id`, `newkey`, `newvalue` (truncated), `value_type`.
- **INFO** `upsert_metadata_completed`: `table`, `id`, `newkey`, `status`, `rows_affected`, `elapsed_seconds`.
- **DEBUG**: SQL template.
- **ERROR** (on exception): `tool_name`, parameters, `error_type`, `error_message`.
- Middleware (`ToolLoggingMiddleware`) additionally logs `tool_call_started` (params, INFO), `tool_call_completed` (INFO), and the serialized response (DEBUG).

## Invariants

- Exactly one record changes per call — `id` is the bigint primary key, so a match is unique.
- Only the `metadata` column is ever written.
- No other MCP tool gains write capability; `query` still rejects non-SELECT SQL.
- Values are bound parameters / JSON-encoded; identifiers are quoted via `psycopg.sql.Identifier`.
