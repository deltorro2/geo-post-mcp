# Phase 0 Research: Upsert Metadata Tool

All Technical Context items were resolvable from the existing codebase and the clarified spec; no `NEEDS CLARIFICATION` remained. The decisions below record the approach and the alternatives considered.

## Decision 1: Atomic JSON merge instead of read-modify-write

- **Decision**: Perform the upsert with a single SQL statement:
  `UPDATE <schema>.<table> SET metadata = COALESCE(metadata::jsonb, '{}'::jsonb) || %(pair)s::jsonb WHERE id = %(id)s`
  where `%(pair)s` is a JSON object string `{"<newkey>": <typed value>}` and `%(id)s` is bound as an integer. The left-hand `metadata::jsonb` cast keeps the merge valid even if a table's `metadata` column is declared `json` rather than `jsonb` (Postgres assignment-casts the jsonb result back on store).
- **Rationale**:
  - The jsonb concatenation operator `||` inserts a new key or overwrites an existing key's value in one operation — exactly the upsert semantics (FR-002, FR-003) — while preserving all other keys (FR-004).
  - `COALESCE(metadata, '{}')` handles a NULL/absent metadata value by creating a fresh object (FR-005).
  - A single statement is inherently atomic and gives "last write wins" with no corruption under concurrency (Edge Cases), avoiding a read-modify-write race.
  - `cur.rowcount` after the UPDATE tells us whether a matching record existed (0 → record not found, FR-008/FR-009 with no data change).
- **Alternatives considered**:
  - *Read row → mutate dict in Python → write back*: extra round-trip and a lost-update race window; rejected.
  - *`jsonb_set(metadata, '{newkey}', value)`*: works for replace but does not create the object cleanly when metadata is NULL without nested COALESCE, and `||` expresses the merge more simply; rejected in favor of `||`.

## Decision 2: Value type detection (FR-012)

- **Decision**: In the tool layer, attempt `json.loads(newvalue)`. If it parses, use the resulting typed value (number, boolean, null, object, array, or even a quoted string); if it raises `json.JSONDecodeError`, treat `newvalue` as a plain string. Then build the pair object with `json.dumps({newkey: parsed})` and bind it as a single `::jsonb` parameter.
- **Rationale**: Implements the clarified auto-detect rule (`"42"` → `42`, `"draft"` → `"draft"`) with stdlib only, no new dependency (Technical Constraints). Building the pair via `json.dumps` guarantees correct escaping of `newkey`/`newvalue`, so they are treated strictly as data (FR-010).
- **Alternatives considered**:
  - *Always-string*: rejected per clarification Q1.
  - *Extra `value_type` parameter*: rejected per clarification Q1 (larger API surface).
  - *`ast.literal_eval`*: Python-literal semantics differ from JSON (e.g. `true`/`null`); rejected in favor of `json.loads` to match the documented JSON contract.

## Decision 2b: `id` is always a bigint primary key

- **Decision**: Treat `id` as always present, always a `bigint`, and always the table's primary key. The MCP tool parameter is typed `id: int`; it is bound directly as an integer query parameter (`WHERE id = %(id)s`). No `::text` cast or string coercion is used.
- **Rationale**:
  - The database convention guarantees `id` exists on every eligible table, so a dedicated "missing id column" eligibility branch is unnecessary (a defensive check may remain but is not expected to trigger).
  - Because `id` is the primary key, a match affects **exactly one** row, satisfying FR-011 without an additional uniqueness guard.
  - Typing the parameter as `int` and binding it as an integer avoids the `operator does not exist: integer = text` failure that would occur if a string were bound against a `bigint` column.
- **Alternatives considered**:
  - *Type the parameter as `str` and compare with `id::text = %s`*: rejected — unnecessary now that `id` is known to be `bigint`; an integer bind is simpler and uses the primary-key index directly.
  - *Auto-detect the PK column name*: rejected — the column is always literally `id` (clarification Q3).

## Decision 3: Safe identifier handling for schema/table

- **Decision**: The `schema` and `table_name` cannot be passed as bound *values*; compose them as quoted identifiers using `psycopg.sql.SQL(...).format(psycopg.sql.Identifier(schema, table_name))`. The `id`, and the JSON pair are passed as bound parameters.
- **Rationale**: Table name is validated against `allowed_tables` before use (FR-007), and `psycopg.sql.Identifier` provides correct quoting — together they prevent SQL injection via the identifier path (Constitution: SQL injection review). Mirrors the project's "parameterized queries only" rule.
- **Alternatives considered**: f-string interpolation of the table name — rejected (injection risk, violates Technical Constraints).

## Decision 4: Eligibility and validation order

- **Decision**: Validate in this order, stopping at the first failure with a clear message and no DB write:
  1. `table_name` is non-empty and bare (no `.`), consistent with `fieldmeaning` validation.
  2. `newkey` is non-empty.
  3. `is_table_allowed(table_name, schema, allowed_tables)` → else access denied (FR-007).
  4. `check_table_exists(conn, schema, table_name)` → else table not found.
  5. Table has a `metadata` column → else table ineligible (Assumptions, US3). The `id` (bigint PK) is guaranteed by convention; a defensive check for it may be included but is not expected to trigger.
  6. Execute UPDATE; if `rowcount == 0` → record not found (FR-008/FR-009).
- **Rationale**: Reuses existing helpers (`is_table_allowed`, `check_table_exists`) for consistency. The column-existence check is the new piece; it reuses the `information_schema.columns` pattern already in `services/schema.py`/`fieldmeaning.py`.
- **Alternatives considered**: Letting the database raise on a missing column — rejected; an explicit pre-check yields the clear, user-facing errors the spec requires (SC-003).

## Decision 5: Read-only guarantee preserved (SC-005)

- **Decision**: `upsert_metadata` does **not** route through `query_tool`/`validate_select_only`. It runs its own dedicated parameterized UPDATE limited to the `metadata` column. No configuration flag gates it (clarification Q2); the write capability is structurally confined to this tool and this column.
- **Rationale**: The existing read-only enforcement lives in `validate_select_only`, applied only by the `query` tool. All other tools (`list_tables`, `describe_table`, `fieldmeaning`) remain read-only because none of them write. Adding one tool with a narrowly scoped UPDATE keeps that property intact and verifiable (a test asserts `query` still rejects non-SELECT).
- **Alternatives considered**: Relaxing `validate_select_only` to allow some UPDATEs — rejected; that would widen the write surface beyond `metadata` and break SC-005.

## Decision 6: Logging approach (user directive + Principle IV)

- **Decision**: Add explicit INFO logs in the tool/service:
  - `upsert_metadata_requested` — `table`, `id`, `newkey`, `newvalue` (truncated like other params), and detected `value_type`.
  - `upsert_metadata_completed` — `table`, `id`, `newkey`, `status` (`updated`/`not_found`), `rows_affected`, `elapsed_seconds`.
  - DEBUG: the SQL template. ERROR (on exception): tool name, params, exception type/message.
  The existing `ToolLoggingMiddleware` still wraps the call (start/complete/error), so parameters and the serialized result are also captured at the middleware layer (INFO params, DEBUG response).
- **Rationale**: Satisfies the user's requirement that "all parameters must be seen in the log and the result," and Constitution Principle IV (INFO for operations, DEBUG for internals, ERROR for failures, structured/JSON logging).
- **Alternatives considered**: Relying solely on middleware — rejected because the middleware logs the full result only at DEBUG; an explicit INFO result log makes the outcome visible at the operational level.

## Open items deferred to implementation

- **metadata column type**: Assumed `jsonb`. The statement now casts the left operand via `metadata::jsonb` (Decision 1), so a `json`-typed column also works. Confirm during implementation against the real schema; a table whose `metadata` is a non-JSON type would make it ineligible.
- **id column type**: Resolved — `id` is always `bigint PRIMARY KEY` (Decision 2b). No outstanding question.
