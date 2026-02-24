# Implementation Plan: Field Meaning Tool

**Branch**: `004-fieldmeaning-tool` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-fieldmeaning-tool/spec.md`

## Summary

Add an MCP tool named `fieldmeaning` that accepts a bare table
name, queries PostgreSQL catalog tables for column comments,
and returns a structured list of column name, data type, and
description for every column in the table. The tool enforces
the allowed-tables list from settings and resolves table names
against the configured schema.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP (MCP Python SDK), psycopg (async PostgreSQL driver), Pydantic
**Storage**: PostgreSQL with PostGIS (read-only schema catalog queries)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux/macOS server
**Project Type**: MCP server (network service)
**Performance Goals**: Schema metadata queries return in <1s for tables with up to 500 columns
**Constraints**: Read-only access; parameterized queries only; no string interpolation for SQL
**Scale/Scope**: Single tool addition to existing MCP server; queries pg_catalog tables

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. MCP Protocol Compliance | PASS | Tool exposes complete JSON Schema for input parameter (FR-007); uses MCP-standard error codes |
| II. Type Safety | PASS | Pydantic model for tool input (table name) and output (FieldMeaningEntry); full type annotations planned |
| III. Syntactic Simplicity | PASS | Single-purpose tool function; schema query is a single SQL statement; no abstractions needed |
| IV. Log Coverage | PASS | FR-008 requires logging invocation with table name and result count; errors logged per constitution |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-fieldmeaning-tool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│   └── fieldmeaning.py  # Pydantic models for tool I/O
├── services/
│   └── fieldmeaning.py  # Schema query logic
├── tools/
│   └── fieldmeaning.py  # MCP tool registration
└── config/
    └── settings.py      # Settings loader (shared, from 003)

tests/
├── integration/
│   └── test_fieldmeaning.py
└── unit/
    └── test_fieldmeaning.py
```

**Structure Decision**: Single project layout. The `fieldmeaning`
tool follows the same pattern as other MCP tools in the server:
model in `models/`, business logic in `services/`, MCP tool
registration in `tools/`.
