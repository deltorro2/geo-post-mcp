---
description: "Task list for Upsert Metadata Tool"
---

# Tasks: Upsert Metadata Tool

**Input**: Design documents from `/specs/003-upsert-metadata/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/upsert_metadata.md, quickstart.md

**Tests**: Included. The project constitution (Principle IV + Development Workflow) requires every MCP tool to have an integration test through the MCP layer and to verify emitted logs, so test tasks are mandatory here.

**Organization**: Tasks are grouped by user story. The core write path (one atomic JSON-merge UPDATE) delivers both insert (US1) and replace (US2); US2's phase therefore focuses on proving replace semantics, and US3 adds the validation/error surface.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Single project: `src/`, `tests/` at repository root (per plan.md Structure Decision).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm environment and place the test fixture all functional tests will use.

- [x] T001 Verify dependencies are present (FastMCP, psycopg, structlog, pydantic) by running `cd src && pytest -q` once to confirm the existing suite passes before changes.
- [x] T002 Add a `test_meta` fixture table (columns: `id bigint PRIMARY KEY`, `name text`, `metadata jsonb`) seeded with at least one row, and register `<schema>.test_meta` in `allowed_tables`, in tests/functional/conftest.py (extend the `test_tables` fixture and `test_settings`). Also add a `test_nometa` table (`id bigint PRIMARY KEY`, no `metadata` column) for ineligibility tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks used by every user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Create `UpsertResult` Pydantic model (`table: str`, `id: str`, `key: str`, `status: str`, `rows_affected: int`) in src/models/upsert.py per data-model.md.
- [x] T004 [P] Implement `parse_value(newvalue: str) -> tuple[object, str]` helper (auto-detect via `json.loads`, fall back to string; return parsed value plus a `value_type` label) in src/tools/upsert.py per research.md Decision 2.
- [x] T005 [P] Implement `has_metadata_column(conn, schema, table_name) -> bool` (returns True when the table has a `metadata` column, using the `information_schema.columns` pattern) in src/services/upsert.py. The `id` bigint PK is guaranteed by convention, so only `metadata` needs checking.

**Checkpoint**: Model, value parser, and eligibility helper exist and are importable.

---

## Phase 3: User Story 1 - Add a new key to a record's metadata (Priority: P1) 🎯 MVP

**Goal**: A caller can add a brand-new key/value to one record's `metadata`; existing keys are preserved; typed values are detected.

**Independent Test**: Call `upsert_metadata` with a new key on a seeded `test_meta` row, then `query` the row and confirm the new pair is present (typed correctly) and prior keys remain.

### Tests for User Story 1 ⚠️

> Write these FIRST and ensure they FAIL before implementation.

- [x] T006 [P] [US1] Unit test `parse_value`: `"42"`→number, `"true"`→bool, `"draft"`→string, `"[1,2]"`→array, `""`→string, in tests/unit/test_upsert_value_parsing.py.
- [x] T007 [P] [US1] Unit test the upsert service with a mocked async connection: assert the executed statement uses the `COALESCE(metadata::jsonb,'{}'::jsonb) || …::jsonb` merge and `WHERE id = …`, that `id` is bound as an integer parameter, and that `rows_affected` comes from `cur.rowcount`. Assert on key fragments/bound params rather than exact string equality (psycopg composes `sql.Composed` objects), in tests/unit/test_upsert_service.py.
- [x] T008 [P] [US1] Functional test (MCP client): add a new key to a `test_meta` row → `status="updated"`, `rows_affected=1`; re-query shows the new pair; a pre-existing key is untouched; `"42"` stored as JSON number, in tests/functional/test_upsert_tool.py.

### Implementation for User Story 1

- [x] T009 [US1] Implement `upsert_metadata(conn, schema, table_name, id: int, pair_json) -> int` in src/services/upsert.py: build the statement with `psycopg.sql.Identifier(schema, table_name)`, use `SET metadata = COALESCE(metadata::jsonb,'{}'::jsonb) || %s::jsonb WHERE id = %s`, bind the JSON pair and the integer `id` as parameters, execute the atomic merge UPDATE, return `cur.rowcount`. DEBUG-log the SQL template and elapsed time (research.md Decisions 1, 2b & 3).
- [x] T010 [US1] Implement `upsert_metadata_tool(table_name, id: int, newkey, newvalue, conn, schema, allowed_tables) -> dict` happy path in src/tools/upsert.py: access check via `is_table_allowed`, parse value via `parse_value`, build `{newkey: value}` with `json.dumps`, call the service, return `UpsertResult(...).model_dump()` with `status` derived from rows affected.
- [x] T011 [US1] Add INFO logging in src/tools/upsert.py: `upsert_metadata_requested` (table, id, newkey, truncated newvalue, value_type) before the write and `upsert_metadata_completed` (table, id, newkey, status, rows_affected, elapsed_seconds) after (contracts/upsert_metadata.md logging contract).
- [x] T012 [US1] Register the `@mcp.tool() async def upsert_metadata(table_name: str, id: int, newkey: str, newvalue: str)` wrapper in src/server.py (mirror existing tools: `_get_connection()`, assert `_settings`, delegate to `upsert_metadata_tool`) with a docstring matching contracts/upsert_metadata.md. If ruff flags `id` shadowing the builtin (A002), add `# noqa: A002`.

**Checkpoint**: New keys can be inserted end-to-end via MCP; US1 functional test passes.

---

## Phase 4: User Story 2 - Replace the value of an existing metadata key (Priority: P1)

**Goal**: Calling the tool with an existing key replaces its value with no duplicate key, leaving other keys intact.

**Independent Test**: Upsert the same key twice with different values on a `test_meta` row; confirm only the latest value remains and no duplicate key exists.

### Tests for User Story 2 ⚠️

- [x] T013 [P] [US2] Unit test the service/SQL confirms the `||` merge overwrites an existing key (mocked conn assertion or documented behavior) in tests/unit/test_upsert_service.py.
- [x] T014 [P] [US2] Functional test: upsert key `"status"` twice (`"draft"` then `"published"`) on a `test_meta` row → final metadata has `"status":"published"`, exactly one `status` entry, and other keys unchanged, in tests/functional/test_upsert_tool.py.

### Implementation for User Story 2

- [x] T015 [US2] Confirm no code change is required (the atomic `||` merge from T009 already overwrites); if the replace functional test reveals a gap (e.g. NULL metadata edge), fix it in src/services/upsert.py.

**Checkpoint**: Both insert and replace work; US1 and US2 functional tests pass.

---

## Phase 5: User Story 3 - Safe handling of invalid requests (Priority: P2)

**Goal**: Invalid requests are rejected with clear messages and zero data change.

**Independent Test**: Call the tool with a non-existent id, a table lacking `metadata`/`id`, and a disallowed table; confirm each yields a clear error/`not_found` and the data is unchanged.

### Tests for User Story 3 ⚠️

- [x] T016 [P] [US3] Functional tests for error paths in tests/functional/test_upsert_tool.py: (a) non-existent id (e.g. a bigint with no row) → `status="not_found"`, `rows_affected=0`, no change; (b) disallowed table → `ToolError`; (c) `test_nometa` (no metadata column) → `ToolError` "not eligible"; (d) empty table name and schema-qualified name → `ToolError`; (e) empty `newkey` → `ToolError`.
- [x] T017 [P] [US3] Functional test asserting the read-only guarantee is intact: `query` with an `UPDATE` statement still raises `ToolError` (SC-005), in tests/functional/test_upsert_tool.py.
- [x] T018 [P] [US3] Logging test: an error invocation emits an ERROR-level structured log with tool/param context (extend tests/functional/test_upsert_tool.py or a unit test of the tool wrapper).

### Implementation for User Story 3

- [x] T019 [US3] Add input validation in src/tools/upsert.py: reject empty/`.`-qualified `table_name` (reuse the `validate_table_name` pattern from src/tools/fieldmeaning.py) and empty `newkey`, before any DB access.
- [x] T020 [US3] Add eligibility checks in src/tools/upsert.py ordered per research.md Decision 4: access denied → table exists (`check_table_exists`) → `has_metadata_column` (else "not eligible for metadata upsert"); ensure each raises `ValueError` with the contract message and performs no write. (`id` presence is guaranteed by the bigint-PK convention.)
- [x] T021 [US3] Map `rows_affected == 0` to `status="not_found"` (no exception) in src/tools/upsert.py, and ensure the ERROR log path includes tool name, parameters, exception type/message on failures.

**Checkpoint**: All three stories function; error and read-only invariants verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T022 [P] Run `cd src && ruff check .` and resolve any lint issues in the new files (src/models/upsert.py, src/services/upsert.py, src/tools/upsert.py).
- [x] T023 [P] Verify type safety: ensure full annotations on all new functions and that the `metadata` jsonb assumption / non-jsonb fallback note from research.md is honored or documented in src/services/upsert.py.
- [x] T024 Run the full suite `cd src && pytest` and the quickstart.md validation steps; confirm functional tests skip cleanly when no DB is available.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational. US1 is the MVP; US2 depends on US1's service/tool (T009–T012); US3 depends on US1's tool wrapper (T010) existing.
- **Polish (Phase 6)**: Depends on all targeted stories being complete.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on other stories. Delivers the MVP.
- **US2 (P1)**: Builds on US1's atomic merge (shared code); independently testable via replace scenario.
- **US3 (P2)**: Builds on US1's tool wrapper; adds the validation/error surface; independently testable via failure scenarios.

### Within Each User Story

- Tests written first and failing before implementation.
- Models/helpers (Phase 2) before services; services before the tool wrapper; tool wrapper before registration.

### Parallel Opportunities

- T003, T004, T005 (Foundational) are different files/functions → parallel.
- US1 tests T006, T007, T008 → parallel (different files).
- US3 tests T016, T017, T018 → parallel (mostly same file; coordinate edits or write sequentially if conflicts).
- T022, T023 (Polish) → parallel.

---

## Parallel Example: User Story 1

```bash
# Write US1 tests together (different files):
Task: "Unit test parse_value in tests/unit/test_upsert_value_parsing.py"
Task: "Unit test upsert service (mocked conn) in tests/unit/test_upsert_service.py"
Task: "Functional insert test in tests/functional/test_upsert_tool.py"

# Foundational building blocks together (different files):
Task: "UpsertResult model in src/models/upsert.py"
Task: "parse_value helper in src/tools/upsert.py"
Task: "check_metadata_columns in src/services/upsert.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → 4. STOP & validate insert end-to-end → demo MVP.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 (insert + typed values) → test → demo (MVP).
3. US2 (replace semantics) → test → demo.
4. US3 (validation, errors, read-only guarantee) → test → demo.

---

## Notes

- [P] = different files, no dependencies.
- The single atomic `||` UPDATE intentionally satisfies both US1 (insert) and US2 (replace); US2 is primarily verification.
- No configuration flag gates the write (clarification Q2); the write path is structurally limited to `upsert_metadata` and the `metadata` column.
- Commit after each task or logical group; verify tests fail before implementing.
