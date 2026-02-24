# Tasks: Field Meaning Tool

**Input**: Design documents from `/specs/004-fieldmeaning-tool/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included — tests were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `src/models/`, `src/services/`, `src/tools/`, `src/config/`, `tests/unit/`, `tests/integration/`
- [ ] T002 Initialize Python project with pyproject.toml — dependencies: fastmcp, psycopg[binary], pydantic, structlog (or python-json-logger for structured logging)
- [ ] T003 [P] Configure mypy strict mode in pyproject.toml and add ruff for linting/formatting

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement settings loader: read `geo-post-mcp-settings.json` and `POSTGISMCPPASS` env var in `src/config/settings.py` — Pydantic model with fields: host, port, user, schema, allowed_tables; password from env var defaulting to empty string
- [ ] T005 [P] Implement structured JSON logging setup in `src/config/logging.py` — configure structlog or logging with JSON formatter; log levels per constitution (DEBUG/INFO/WARNING/ERROR)
- [ ] T006 [P] Implement database connection helper in `src/services/database.py` — async connection pool using psycopg with settings from T004; parameterized queries only
- [ ] T007 Implement allowed-tables check utility in `src/services/access_control.py` — function that takes a table name and settings, returns True/False; reusable across all MCP tools

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Retrieve Field Meanings (Priority: P1) MVP

**Goal**: User calls `fieldmeaning` with a table name and receives column names, data types, and schema comment descriptions for every column.

**Independent Test**: Create a table with column comments, invoke `fieldmeaning`, verify all columns returned with correct descriptions. Also test: table with no comments, nonexistent table, schema-qualified name rejection.

### Implementation for User Story 1

- [ ] T008 [P] [US1] Create Pydantic models in `src/models/fieldmeaning.py` — `FieldMeaningRequest` (table_name: str, with dot-rejection validator), `FieldMeaningEntry` (column_name, data_type, ordinal_position, description: str | None), `FieldMeaningResponse` (table, schema, columns: list[FieldMeaningEntry])
- [ ] T009 [US1] Implement schema query service in `src/services/fieldmeaning.py` — async function that: (1) validates table_name has no dot (raise error for schema-qualified), (2) checks table existence via information_schema.tables, (3) queries information_schema.columns + pg_catalog.pg_description + pg_catalog.pg_statio_all_tables for column comments per research.md R1 query pattern, (4) returns list of FieldMeaningEntry ordered by ordinal_position; uses parameterized queries only
- [ ] T010 [US1] Register MCP tool in `src/tools/fieldmeaning.py` — use `@mcp.tool()` decorator to register `fieldmeaning` function; accept FieldMeaningRequest input; call service from T009; serialize FieldMeaningResponse as JSON text content; log invocation at INFO level with table_name and result column count per FR-008; log errors at ERROR level with full context
- [ ] T011 [US1] Wire tool into MCP server entrypoint in `src/server.py` — import and register the fieldmeaning tool; configure FastMCP app with Streamable HTTP transport; ensure tool appears in MCP tool catalog with complete JSON Schema (FR-007)

**Checkpoint**: At this point, `fieldmeaning` is functional for any table the database user can access. MVP complete.

---

## Phase 4: User Story 2 — Respect Table Access Restrictions (Priority: P2)

**Goal**: The `fieldmeaning` tool checks the allowed-tables list from settings and rejects requests for tables not on the list.

**Independent Test**: Configure allowed_tables with specific tables. Call `fieldmeaning` for an allowed table (succeeds) and a disallowed table (rejected with clear error message).

### Implementation for User Story 2

- [ ] T012 [US2] Add allowed-tables enforcement to fieldmeaning service in `src/services/fieldmeaning.py` — before any DB query, call access_control check from T007; if table not allowed, raise error with message "Table '{name}' is not in the allowed tables list" per contract; add INFO log for rejected requests
- [ ] T013 [US2] Update MCP tool handler in `src/tools/fieldmeaning.py` — catch access-denied errors from service and return MCP tool error response with the rejection message

**Checkpoint**: `fieldmeaning` now enforces table access restrictions consistent with other server tools.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T014 Run mypy --strict on all source files and fix any type errors
- [ ] T015 Run ruff linter/formatter on all source files and fix any issues
- [ ] T016 Validate against quickstart.md scenarios in `specs/004-fieldmeaning-tool/quickstart.md` — manually verify all 8 verification steps pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T009 service exists before adding access control to it)
- **Polish (Phase 5)**: Depends on all user stories being complete

### Within Each User Story

- Models (T008) before services (T009)
- Services (T009) before tool registration (T010)
- Tool registration (T010) before server wiring (T011)

### Parallel Opportunities

- T003 can run in parallel with T001/T002 (different files)
- T005 and T006 can run in parallel (different files, both depend on T004)
- T008 can run in parallel with foundational tasks (model file is independent)

---

## Parallel Example: Foundational Phase

```bash
# After T004 (settings) completes, launch in parallel:
Task: "Implement structured JSON logging in src/config/logging.py"
Task: "Implement database connection helper in src/services/database.py"
Task: "Implement allowed-tables check in src/services/access_control.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test fieldmeaning with a real PostgreSQL/PostGIS database
5. Verify columns with comments, without comments, nonexistent table, schema-qualified rejection

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> MVP!
3. Add User Story 2 -> Test access control -> Full feature complete
4. Polish -> Type check, lint, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 2 depends on User Story 1 (adds access control to existing service)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
