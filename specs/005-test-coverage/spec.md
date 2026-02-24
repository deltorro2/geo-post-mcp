# Feature Specification: Test Coverage

**Feature Branch**: `005-test-coverage`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "All main parts of the system should be covered by unit tests. All tools should be covered by functional tests."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unit Tests for Core Components (Priority: P1)

A developer makes changes to any core component of the system
(settings loading, database connection management, SQL
validation, access control, schema query logic, logging setup)
and runs the unit test suite. The tests execute quickly without
requiring a live database and verify that each component
behaves correctly in isolation. This catches regressions early
and documents expected behavior.

**Why this priority**: Unit tests are the fastest feedback loop
for developers. They cover the foundational components that
all features depend on, making them the highest-value tests
to write first.

**Independent Test**: Can be verified by running the unit test
suite and confirming all tests pass. Each test runs without
external dependencies (database, network). Delivers value by
ensuring core logic is correct before integration.

**Acceptance Scenarios**:

1. **Given** the settings loader component,
   **When** unit tests are run,
   **Then** they verify: valid settings file parsing, missing
   file error, missing required fields error, malformed values
   error, environment variable password loading, empty password
   default, and unrecognized field warning.

2. **Given** the SQL validation component,
   **When** unit tests are run,
   **Then** they verify: SELECT statements are accepted,
   non-SELECT statements (INSERT, UPDATE, DELETE, DROP, CREATE,
   ALTER, TRUNCATE) are rejected, and edge cases (comments,
   CTEs, subqueries) are handled correctly.

3. **Given** the access control component,
   **When** unit tests are run,
   **Then** they verify: allowed tables are accepted, disallowed
   tables are rejected, empty allowed list rejects all, and
   table name matching is case-sensitive.

4. **Given** the fieldmeaning schema query logic,
   **When** unit tests are run,
   **Then** they verify: bare table name validation passes,
   schema-qualified names (containing dots) are rejected,
   empty table names are rejected, and response model
   serialization is correct.

5. **Given** any unit test,
   **When** it is run,
   **Then** it completes without requiring a running database,
   network connection, or any external service.

---

### User Story 2 - Functional Tests for MCP Tools (Priority: P2)

A developer runs the functional test suite to verify that each
MCP tool works end-to-end through the MCP protocol layer
against a real database. The tests exercise the complete path:
MCP client request, tool invocation, database query, response
serialization, and error handling. This validates that all
components integrate correctly and the tools behave as
documented in their contracts.

**Why this priority**: Functional tests verify the system works
as a whole. They depend on the components validated by unit
tests (US1) and require a running database, so they are slower
but catch integration issues that unit tests cannot.

**Independent Test**: Can be verified by starting the MCP
server with a test database, running the functional test suite,
and confirming all tool interactions produce expected results
per the MCP tool contracts.

**Acceptance Scenarios**:

1. **Given** the SQL query execution tool and a test database
   with sample data,
   **When** functional tests are run,
   **Then** they verify: simple SELECT returns correct rows,
   complex queries (JOINs, aggregations, CTEs) return correct
   results, non-SELECT statements are rejected with MCP error,
   nonexistent table returns clear error, result row limit is
   enforced, and query execution is logged.

2. **Given** the SQL query tool and a test database with
   PostGIS data,
   **When** functional tests are run,
   **Then** they verify: spatial queries (ST_Distance,
   ST_Contains, ST_DWithin) return correct results, geometry
   columns are returned as GeoJSON, and PostGIS functions work
   through the MCP tool interface.

3. **Given** the schema discovery tool and a test database,
   **When** functional tests are run,
   **Then** they verify: tables are listed with schema grouping,
   column details include name/type/nullability, and spatial
   columns include geometry type and SRID.

4. **Given** the fieldmeaning tool and a test database with
   column comments,
   **When** functional tests are run,
   **Then** they verify: columns with comments return
   descriptions, columns without comments return null
   description, nonexistent tables return error, disallowed
   tables are rejected, and schema-qualified names are rejected.

5. **Given** any MCP tool functional test,
   **When** a disallowed table is referenced,
   **Then** the test verifies the tool returns an access-denied
   error before any database query executes.

---

### User Story 3 - Test Infrastructure and Execution (Priority: P3)

A developer can run the full test suite with a single command.
Unit tests run without external dependencies. Functional tests
use a dedicated test database that is set up and torn down
automatically. Test results clearly indicate which tests
passed, failed, and were skipped, with enough detail to
diagnose failures.

**Why this priority**: Test infrastructure enables US1 and US2
to be practical and repeatable. Without it, running tests
would require manual setup, reducing their value.

**Independent Test**: Can be verified by running the test
command and confirming: unit tests execute without database,
functional tests connect to the test database, results are
clear, and no test state leaks between runs.

**Acceptance Scenarios**:

1. **Given** the test suite is configured,
   **When** a developer runs the unit tests,
   **Then** all unit tests execute without any external service
   running and complete in under 30 seconds.

2. **Given** a test database is available,
   **When** a developer runs the functional tests,
   **Then** test fixtures create necessary tables, data, and
   column comments before tests and clean up afterward.

3. **Given** the full test suite,
   **When** a developer runs all tests,
   **Then** the output shows pass/fail counts per test category
   (unit vs functional) and any failure includes the test name,
   assertion details, and relevant context.

4. **Given** functional tests that modify database state,
   **When** tests complete (whether passing or failing),
   **Then** all test data is rolled back or cleaned up so tests
   are fully isolated from each other.

---

### Edge Cases

- What happens when functional tests run but no test database
  is available? Tests MUST be skipped with a clear message
  rather than failing with a connection error.
- What happens when a unit test accidentally depends on
  external state? The test MUST be flagged during review as
  violating the "no external dependencies" requirement.
- What happens when test data conflicts with existing database
  content? Test fixtures MUST use a dedicated test schema or
  unique table names to avoid conflicts.
- What happens when a new MCP tool is added? The test coverage
  requirement MUST be documented so developers know functional
  tests are mandatory for every tool.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every core component (settings loader, database
  connection manager, SQL validator, access control checker,
  schema query service, fieldmeaning service, logging setup)
  MUST have unit tests that run without external dependencies.
- **FR-002**: Every MCP tool (SQL query execution, geospatial
  query execution, schema discovery, fieldmeaning) MUST have
  functional tests that exercise the tool through the MCP
  protocol interface against a real database.
- **FR-003**: Unit tests MUST use mocks or stubs for database
  interactions, file I/O, and environment variables to ensure
  isolation.
- **FR-004**: Functional tests MUST use a dedicated test
  database with fixtures that create and clean up test data
  (tables, column comments, spatial data) automatically.
- **FR-005**: Functional tests MUST verify both success paths
  and error paths for each tool (valid input, invalid input,
  access denied, nonexistent resources).
- **FR-006**: Functional tests MUST verify that structured log
  entries are emitted for tool invocations and errors, per
  the constitution's log coverage principle.
- **FR-007**: Unit tests MUST complete in under 30 seconds
  total without any external service running.
- **FR-008**: Functional tests MUST skip gracefully with a
  clear message when no test database is available.
- **FR-009**: All tests MUST be runnable with a single command
  from the project root.
- **FR-010**: Test isolation MUST be enforced — no test may
  depend on the execution order or side effects of another
  test.

## Assumptions

- Unit tests mock database interactions using standard
  mocking patterns (mock objects, dependency injection).
- Functional tests require a running PostgreSQL instance with
  PostGIS extension; this is expected in CI environments and
  developer machines.
- Test database credentials are configured via environment
  variables or a test-specific settings file.
- The test suite is organized into separate directories for
  unit and functional tests to allow running them independently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of core components have at least one unit
  test covering their primary success path and at least one
  error path.
- **SC-002**: 100% of MCP tools have functional tests covering
  success, error, and access-denied scenarios.
- **SC-003**: The full unit test suite runs in under 30 seconds
  without any external service.
- **SC-004**: Functional tests can be run independently from
  unit tests and vice versa.
- **SC-005**: A new developer can run the full test suite
  within 10 minutes of cloning the repository (given a
  database is available).
- **SC-006**: All tests pass on every commit — zero tolerance
  for flaky or intermittent failures.
