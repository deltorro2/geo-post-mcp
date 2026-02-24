# Tasks: Test Coverage

**Input**: Design documents from `/specs/005-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: This feature IS the test suite. All tasks produce test code.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test directory structure and pytest configuration

- [ ] T001 Create test directory structure: `tests/`, `tests/unit/`, `tests/functional/`, with `__init__.py` in each
- [ ] T002 Add test dependencies to pyproject.toml: pytest, pytest-asyncio, mcp (client SDK) in `[project.optional-dependencies.test]` section
- [ ] T003 Configure pytest in pyproject.toml: register `unit` and `functional` markers; set testpaths to `tests/`; configure asyncio_mode = "auto"

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared fixtures and infrastructure that ALL test stories depend on

**CRITICAL**: No test implementation can begin until this phase is complete

- [ ] T004 Create root conftest in `tests/conftest.py` — register `unit` and `functional` markers; add `auto_unit_marker` autouse fixture that applies `@pytest.mark.unit` to all tests in `tests/unit/`; add `auto_functional_marker` autouse fixture for `tests/functional/`
- [ ] T005 [P] Create unit test conftest in `tests/unit/conftest.py` — shared mock fixtures: `mock_settings` (returns a valid Settings Pydantic model with test values), `mock_db_connection` (AsyncMock for psycopg connection), `mock_allowed_tables` (returns `["test_parcels", "test_buildings"]`)
- [ ] T006 [P] Create functional test conftest in `tests/functional/conftest.py` — session-scoped fixture `db_settings` that reads `geo-post-mcp-settings.json` and `POSTGISMCPPASS` env var using the production settings loader; session-scoped fixture `db_connection` that attempts to connect and skips all functional tests with message "Skipping functional tests: database not available" if connection fails; session-scoped fixture `mcp_client` that starts the MCP server in-process (FastMCP test client) and returns an MCP client connected to it; function-scoped fixture `test_tables` that creates `test_parcels`, `test_buildings`, `test_restricted` tables per data-model.md with sample data and column comments, yields, then drops them on teardown

**Checkpoint**: Test infrastructure ready — unit and functional tests can now be written

---

## Phase 3: User Story 1 — Unit Tests for Core Components (Priority: P1) MVP

**Goal**: Every core component has unit tests covering success and error paths, running without external dependencies.

**Independent Test**: Run `pytest -m unit` — all tests pass without any database or network service running, completing in under 30 seconds.

### Implementation for User Story 1

- [ ] T007 [P] [US1] Write settings loader unit tests in `tests/unit/test_settings.py` — test cases: (1) valid JSON file parsed correctly, (2) missing file raises FileNotFoundError with expected message, (3) missing required field (host) raises validation error, (4) malformed port (string instead of int) raises validation error, (5) POSTGISMCPPASS env var read as password, (6) missing POSTGISMCPPASS defaults to empty string, (7) unrecognized field in JSON logs warning but succeeds. Use tmp_path for temp settings files, monkeypatch for env vars.
- [ ] T008 [P] [US1] Write SQL validator unit tests in `tests/unit/test_sql_validator.py` — test cases: (1) simple SELECT accepted, (2) SELECT with JOINs/WHERE/GROUP BY/ORDER BY accepted, (3) SELECT with CTE (WITH clause) accepted, (4) SELECT with subquery accepted, (5) INSERT rejected, (6) UPDATE rejected, (7) DELETE rejected, (8) DROP TABLE rejected, (9) CREATE TABLE rejected, (10) ALTER TABLE rejected, (11) TRUNCATE rejected, (12) SELECT with leading comment accepted, (13) case-insensitive detection (select vs SELECT). No DB mocks needed — pure string validation.
- [ ] T009 [P] [US1] Write access control unit tests in `tests/unit/test_access_control.py` — test cases: (1) table in allowed list returns True, (2) table not in allowed list returns False, (3) empty allowed list rejects all tables, (4) case-sensitive matching (Parcels != parcels), (5) table name with spaces rejected. Use `mock_allowed_tables` fixture.
- [ ] T010 [P] [US1] Write fieldmeaning service unit tests in `tests/unit/test_fieldmeaning_service.py` — test cases: (1) bare table name "parcels" passes validation, (2) schema-qualified name "public.parcels" rejected with error, (3) empty table name rejected, (4) table name with dot rejected, (5) FieldMeaningEntry model serializes correctly with description, (6) FieldMeaningEntry model serializes correctly with null description, (7) FieldMeaningResponse model serializes correctly with column list. Use mocked DB connection for any query tests.
- [ ] T011 [P] [US1] Write schema query service unit tests in `tests/unit/test_schema_service.py` — test cases: (1) table existence check returns True for existing table (mock DB returns row), (2) table existence check returns False for missing table (mock DB returns empty), (3) column query returns expected FieldMeaningEntry list from mocked result rows, (4) column query with no comments returns null descriptions. Use `mock_db_connection` fixture.
- [ ] T012 [P] [US1] Write logging setup unit tests in `tests/unit/test_logging.py` — test cases: (1) logging is configured with JSON structured format, (2) INFO level log entry contains expected fields (tool name, parameters), (3) ERROR level log entry contains exception type and message, (4) sensitive values (password) are not present in log output. Use caplog fixture.
- [ ] T013 [P] [US1] Write database connection manager unit tests in `tests/unit/test_database.py` — test cases: (1) connection pool created with correct settings (host, port, user, password, dbname), (2) connection failure raises expected exception, (3) connection parameters match settings model values. Use mocked psycopg connection.

**Checkpoint**: All core components have unit tests. Run `pytest -m unit` — all pass in <30s with no external services.

---

## Phase 4: User Story 2 — Functional Tests for MCP Tools (Priority: P2)

**Goal**: Every MCP tool has functional tests exercising the tool through the MCP client against a real database.

**Independent Test**: Run `pytest -m functional` with a test database available — all tests pass. Run without database — all tests skip with clear message.

### Implementation for User Story 2

- [ ] T014 [US2] Write SQL query execution tool functional tests in `tests/functional/test_query_tool.py` — use `mcp_client` and `test_tables` fixtures; test cases: (1) `call_tool("query", {"sql": "SELECT * FROM test_parcels"})` returns rows with correct column names and values, (2) complex query with JOIN between test_parcels and test_buildings returns correct results, (3) aggregation query (COUNT, SUM) returns correct values, (4) CTE query returns correct results, (5) non-SELECT statement (INSERT) returns MCP error, (6) query on nonexistent table returns error, (7) query on `test_restricted` (disallowed table) returns access-denied error, (8) query exceeding row limit returns truncated results with indicator, (9) verify INFO log emitted for query execution via caplog
- [ ] T015 [US2] Write geospatial query tool functional tests in `tests/functional/test_geo_query_tool.py` — use `mcp_client` and `test_tables` fixtures; test cases: (1) `SELECT ST_AsGeoJSON(geom) FROM test_parcels` returns valid GeoJSON strings, (2) spatial query with ST_DWithin returns parcels within radius, (3) spatial join with ST_Contains between test_parcels and test_buildings returns correct matches, (4) ST_Distance query returns correct distance values, (5) geometry columns in SELECT * are returned as GeoJSON (not WKB), (6) verify INFO log emitted for geo query
- [ ] T016 [US2] Write schema discovery tool functional tests in `tests/functional/test_schema_tool.py` — use `mcp_client` and `test_tables` fixtures; test cases: (1) `call_tool("list_tables", {})` returns test_parcels and test_buildings (allowed tables), (2) list_tables does NOT include test_restricted, (3) `call_tool("describe_table", {"table_name": "test_parcels"})` returns columns with correct names and types, (4) spatial columns include geometry type and SRID, (5) nullability and default values reported correctly, (6) nonexistent table returns error, (7) verify INFO log emitted
- [ ] T017 [US2] Write fieldmeaning tool functional tests in `tests/functional/test_fieldmeaning_tool.py` — use `mcp_client` and `test_tables` fixtures; test cases: (1) `call_tool("fieldmeaning", {"table_name": "test_parcels"})` returns all 4 columns with correct descriptions (gid, name have comments; area_sqm has null), (2) columns are ordered by ordinal position, (3) data_type field matches expected types, (4) nonexistent table returns error, (5) disallowed table `test_restricted` returns access-denied error, (6) schema-qualified name `public.test_parcels` returns rejection error, (7) verify INFO log emitted with table name and column count

**Checkpoint**: All MCP tools have functional tests covering success, error, and access-denied paths. Run `pytest -m functional` — all pass with test database.

---

## Phase 5: User Story 3 — Test Infrastructure and Execution (Priority: P3)

**Goal**: Developer can run tests with simple commands, with clear output and reliable behavior.

**Independent Test**: Run `pytest` — both unit and functional tests execute. Run `pytest -m unit` — only unit tests run without DB. Run `pytest -m functional` without DB — all functional tests skip cleanly.

### Implementation for User Story 3

- [ ] T018 [US3] Add test execution commands to pyproject.toml `[tool.pytest.ini_options]` — configure `markers`, `testpaths`, `asyncio_mode`; add `filterwarnings` to suppress noisy warnings; ensure `pytest` alone runs all tests, `pytest -m unit` runs unit only, `pytest -m functional` runs functional only
- [ ] T019 [US3] Verify graceful skip behavior in `tests/functional/conftest.py` — ensure the session-scoped DB connection fixture properly catches connection exceptions and calls `pytest.skip("Skipping functional tests: database not available")` for the entire functional test session; verify skip message appears in test output
- [ ] T020 [US3] Verify test isolation — run functional tests twice in sequence and confirm: (1) no test data persists between runs, (2) test order does not affect results (run with `pytest -p no:randomly` and `pytest --randomly-seed=12345` if pytest-randomly installed), (3) each test starts with a clean database state

**Checkpoint**: Full test infrastructure validated. Single-command execution works for all, unit-only, and functional-only modes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T021 Run `pytest -m unit` and verify all unit tests pass without any external service
- [ ] T022 Run `pytest -m functional` with test database and verify all functional tests pass
- [ ] T023 Run `mypy --strict` on all test files in `tests/` and fix type errors
- [ ] T024 Validate against quickstart.md scenarios in `specs/005-test-coverage/quickstart.md` — verify all 6 verification steps pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004, T005 for mock fixtures)
- **User Story 2 (Phase 4)**: Depends on Foundational (T004, T006 for DB fixtures and MCP client) and ideally on US1 (unit tests validate components before functional tests exercise them)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 (needs tests to exist before validating infrastructure)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within Each User Story

- US1: All unit test files are independent ([P]) — can be written in parallel
- US2: Functional tests can be written in parallel BUT share DB fixtures; T014-T017 are ordered for logical progression but technically independent
- US3: Configuration and validation tasks are sequential

### Parallel Opportunities

- T005 and T006 (unit vs functional conftest) can run in parallel
- T007-T013 (all unit test modules) can ALL run in parallel — they test different components in different files
- T014-T017 (functional test modules) can run in parallel if DB fixtures are session-scoped

---

## Parallel Example: Unit Tests (Phase 3)

```bash
# All unit test modules can be written simultaneously:
Task: "Write settings loader unit tests in tests/unit/test_settings.py"
Task: "Write SQL validator unit tests in tests/unit/test_sql_validator.py"
Task: "Write access control unit tests in tests/unit/test_access_control.py"
Task: "Write fieldmeaning service unit tests in tests/unit/test_fieldmeaning_service.py"
Task: "Write schema service unit tests in tests/unit/test_schema_service.py"
Task: "Write logging unit tests in tests/unit/test_logging.py"
Task: "Write database connection unit tests in tests/unit/test_database.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (directory structure, dependencies)
2. Complete Phase 2: Foundational (conftest files with fixtures)
3. Complete Phase 3: Unit tests for all 7 core components
4. **STOP and VALIDATE**: Run `pytest -m unit` — all pass in <30s
5. Core component correctness is now verified

### Incremental Delivery

1. Complete Setup + Foundational -> Test infrastructure ready
2. Add User Story 1 (unit tests) -> Run `pytest -m unit` -> MVP!
3. Add User Story 2 (functional tests) -> Run `pytest -m functional` -> Full tool coverage
4. Add User Story 3 (infrastructure validation) -> Run `pytest` -> Everything works together
5. Polish -> Type check, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each unit test module is fully independent and can be written in parallel
- Functional tests share DB fixtures but test different tools
- Commit after each task or logical group
- Stop at any checkpoint to validate test coverage independently
- All test file names follow `test_*.py` convention for pytest auto-discovery
