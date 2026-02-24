# Implementation Plan: Test Coverage

**Branch**: `005-test-coverage` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-test-coverage/spec.md`

## Summary

Add comprehensive test coverage for the geo-post-mcp server.
Unit tests (pytest) cover all core components in isolation
without external dependencies. Functional tests (pytest) cover
all MCP tools and APIs end-to-end using an MCP client that
calls each API sequentially against a real PostgreSQL/PostGIS
database. Database settings for tests are read from the same
`geo-post-mcp-settings.json` file and `POSTGISMCPPASS`
environment variable used by the production server.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pytest, pytest-asyncio, mcp (MCP Python SDK client), unittest.mock
**Storage**: PostgreSQL with PostGIS (test database, same config as production)
**Testing**: pytest for both unit and functional tests
**Target Platform**: Linux/macOS server
**Project Type**: Test suite for MCP server
**Performance Goals**: Unit tests complete in <30s; functional tests complete in <5min
**Constraints**: Unit tests MUST NOT require external services; functional tests use real DB via same settings file
**Scale/Scope**: ~7 unit test modules (one per component), ~4 functional test modules (one per MCP tool/API)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. MCP Protocol Compliance | PASS | Functional tests use MCP client to exercise tools through the protocol layer, validating compliance |
| II. Type Safety | PASS | Test code uses full type annotations; test fixtures use Pydantic models |
| III. Syntactic Simplicity | PASS | Tests follow arrange-act-assert pattern; each test function tests one behavior |
| IV. Log Coverage | PASS | FR-006 requires functional tests to verify structured log entries are emitted |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-test-coverage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tests/
├── conftest.py              # Shared fixtures, pytest markers
├── unit/
│   ├── conftest.py          # Unit test fixtures (mocks)
│   ├── test_settings.py     # Settings loader unit tests
│   ├── test_sql_validator.py    # SQL validation unit tests
│   ├── test_access_control.py   # Access control unit tests
│   ├── test_fieldmeaning_service.py  # Fieldmeaning service unit tests
│   ├── test_schema_service.py   # Schema query service unit tests
│   ├── test_logging.py      # Logging setup unit tests
│   └── test_database.py     # DB connection manager unit tests
├── functional/
│   ├── conftest.py          # Functional test fixtures (DB setup, MCP client)
│   ├── test_query_tool.py   # SQL query execution tool tests
│   ├── test_geo_query_tool.py   # Geospatial query tool tests
│   ├── test_schema_tool.py  # Schema discovery tool tests
│   └── test_fieldmeaning_tool.py  # Fieldmeaning tool tests
└── pytest.ini               # (or pyproject.toml section) markers, paths
```

**Structure Decision**: Single project layout with `tests/unit/`
and `tests/functional/` directories. Unit tests use mocks;
functional tests use an MCP client against a real server + DB.
Both test categories share a root `conftest.py` for common
markers and configuration.
