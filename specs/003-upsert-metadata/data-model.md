# Phase 1 Data Model: Upsert Metadata Tool

## Database entities (existing, not created by this feature)

### Target record / table

A row in an `allowed_tables` PostgreSQL table that exposes:

| Column     | Type   | Role                                                        |
|------------|--------|------------------------------------------------------------|
| `id`       | bigint PRIMARY KEY | Identity column matched against the `id` parameter (exact equality). Always present; uniquely identifies exactly one row. |
| `metadata` | jsonb  | The JSON object holding key/value pairs to upsert. May be NULL/absent → treated as `{}`. |

Eligibility rules (validated, not mutated):
- Table must be in `allowed_tables` (schema-qualified) — else access denied.
- Table must exist in the configured schema — else not found.
- Table must have a `metadata` column — else ineligible. The `id` (bigint PK) is guaranteed by database convention; a defensive check may remain but is not expected to trigger.

State transition for one call (single atomic UPDATE):

```
metadata (before)            newkey/newvalue            metadata (after)
---------------------------  -------------------------  ----------------------------------
NULL                         "source" / "survey-2026"   {"source": "survey-2026"}
{"a": 1}                     "source" / "survey-2026"   {"a": 1, "source": "survey-2026"}   (insert)
{"status": "draft"}          "status" / "published"     {"status": "published"}             (replace)
{"x": 1, "y": 2}             "y" / 9                     {"x": 1, "y": 9}                    (other keys preserved)
```

## Tool input

| Parameter    | Type | Required | Validation                                        |
|--------------|------|----------|---------------------------------------------------|
| `table_name` | str  | yes      | Non-empty; bare name (no `.` schema qualifier).   |
| `id`         | int  | yes      | Bound directly as an integer parameter; matched on the `bigint` primary-key `id` column. |
| `newkey`     | str  | yes      | Non-empty; stored verbatim as a JSON object key.  |
| `newvalue`   | str  | yes      | Type-detected (see below). Empty string allowed.  |

### `newvalue` type detection (FR-012)

```
parsed = json.loads(newvalue)   # success → use parsed typed value
                                #   "42" → 42 (number)
                                #   "true" → true (boolean)
                                #   "null" → null
                                #   "[1,2]" → array, "{...}" → object
                                #   "\"hi\"" → "hi" (string)
except JSONDecodeError:
parsed = newvalue               # plain text, e.g. "draft" → "draft"
```

`value_type` (one of: `number`, `boolean`, `null`, `array`, `object`, `string`) is computed for logging only.

## Tool output — `UpsertResult` (new Pydantic model, `src/models/upsert.py`)

| Field          | Type | Meaning                                                       |
|----------------|------|--------------------------------------------------------------|
| `table`        | str  | Bare table name acted upon.                                  |
| `id`           | int  | The record id targeted.                                     |
| `key`          | str  | The key inserted/replaced.                                  |
| `status`       | str  | `"updated"` when one row changed, `"not_found"` when no row matched. |
| `rows_affected`| int  | Number of rows changed (0 or 1).                            |

Serialized via `model_dump()` to a `dict[str, object]`, matching the return shape of the other tools.

## Error conditions (no data change)

| Condition                                   | Surfaced as |
|---------------------------------------------|-------------|
| Empty/qualified `table_name`, empty `newkey`| `ValueError` → MCP `ToolError` |
| Table not in `allowed_tables`               | `ValueError` "Access denied: …" |
| Table does not exist                        | `ValueError` "Table '…' does not exist …" |
| Table lacks a `metadata` column             | `ValueError` "Table '…' is not eligible for metadata upsert …" |
| No record matches `id` (`rowcount == 0`)    | Returned as `status="not_found"`, `rows_affected=0` (no exception, no change) |
