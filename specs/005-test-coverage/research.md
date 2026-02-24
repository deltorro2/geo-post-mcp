# Research: Test Coverage

**Branch**: `005-test-coverage`
**Date**: 2026-02-23

## R1: MCP Client for Functional Tests

**Decision**: Use the official `mcp` Python SDK client to
connect to the MCP server in functional tests. The client
calls `list_tools()` to discover tools, then `call_tool()`
for each tool under test.

**Rationale**: Using an actual MCP client validates the full
protocol path (serialization, JSON Schema, error codes)
rather than testing internal functions directly. This aligns
with the constitution's MCP Protocol Compliance principle and
the user's requirement for MCP client-based functional tests.

**Alternatives considered**:
- Direct function calls: Faster but bypasses MCP protocol
  layer, missing serialization and schema validation bugs.
- HTTP client (requests/httpx): Tests HTTP transport but not
  MCP protocol semantics. Lower level than needed.

## R2: Test Database Configuration

**Decision**: Functional tests read database settings from the
same `geo-post-mcp-settings.json` file and `POSTGISMCPPASS`
environment variable used by the production server. A test-
specific settings file can be pointed to via an environment
variable (e.g., `GEO_POST_MCP_SETTINGS`) or by placing the
file in the test working directory.

**Rationale**: Per user requirement, tests use the same
configuration mechanism as production. This ensures the
settings loader itself is exercised during functional tests
and reduces configuration drift.

**Alternatives considered**:
- Separate test configuration mechanism: Would require
  maintaining two config paths and could miss bugs in the
  settings loader.
- Hardcoded test credentials: Not portable across environments.

## R3: Test Isolation Strategy

**Decision**: Use pytest fixtures with transaction rollback
for functional test isolation. Each test runs within a
database transaction that is rolled back after the test
completes, ensuring no state leaks between tests.

**Rationale**: Transaction rollback is faster than
CREATE/DROP for each test and guarantees isolation. It works
well with PostgreSQL's transactional DDL support.

**Alternatives considered**:
- Separate test schema per test: High overhead, complex
  setup/teardown.
- Truncate tables between tests: Risk of missing cleanup;
  slower than rollback.

## R4: Pytest Organization and Markers

**Decision**: Use pytest markers to separate unit and
functional tests:
- `@pytest.mark.unit` for unit tests (default, no DB needed)
- `@pytest.mark.functional` for functional tests (requires DB)
- Configure in pyproject.toml to run categories independently:
  `pytest -m unit` or `pytest -m functional`

**Rationale**: Markers allow selective execution. Unit tests
run fast without DB. Functional tests can be skipped in
environments without a database by auto-skipping when the
DB connection fails.

**Alternatives considered**:
- Directory-based selection only (`pytest tests/unit/`):
  Works but markers are more flexible and can be combined
  with other filters.

## R5: Functional Test Skip on Missing Database

**Decision**: Use a session-scoped pytest fixture that
attempts to connect to the database at the start of the
functional test session. If connection fails, all functional
tests are skipped with a clear message:
"Skipping functional tests: database not available."

**Rationale**: Per FR-008, functional tests MUST skip
gracefully. A session-scoped check avoids per-test connection
overhead and provides a single clear message.

## R6: Log Verification in Functional Tests

**Decision**: Use pytest's `caplog` fixture or a custom log
capture fixture to assert that structured log entries are
emitted during tool invocations. Verify: INFO log for tool
call, DEBUG log for DB query, ERROR log for failures.

**Rationale**: Constitution Principle IV requires log coverage.
FR-006 requires functional tests to verify logging. `caplog`
is pytest's built-in mechanism and requires no additional
dependencies.

**Alternatives considered**:
- Custom log handler: More complex, not justified when
  `caplog` is available.

## R7: MCP Server Startup for Functional Tests

**Decision**: Start the MCP server in-process using FastMCP's
test client or by spawning the server as a subprocess and
connecting the MCP client to it. Prefer in-process test
client if FastMCP provides one, as it avoids port management
and is faster.

**Rationale**: In-process testing is faster and more reliable
for CI. If FastMCP supports `mcp.run(test=True)` or similar,
use that. Otherwise, subprocess with a random port.

**Alternatives considered**:
- Always use subprocess: Slower, requires port allocation,
  but tests the full HTTP transport path. Can be added as a
  separate integration test layer later if needed.
