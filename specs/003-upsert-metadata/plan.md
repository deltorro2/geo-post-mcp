# Implementation Plan: Upsert Metadata Tool

**Branch**: `003-upsert-metadata` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-upsert-metadata/spec.md`

## Summary

Add a new MCP tool, `upsert_metadata(table_name, id, newkey, newvalue)`, that inserts or replaces a single key/value pair in the `metadata` (jsonb) column of one record, identified by the table's `id` column. **`id` is always a `bigint` primary key**, so it uniquely identifies exactly one row and the tool parameter is typed as an integer (`id: int`) — bound directly as a query parameter with no type-coercion risk. The write is performed by a single parameterized, atomic SQL `UPDATE` that merges the new pair into the existing JSON (`COALESCE(metadata::jsonb,'{}'::jsonb) || new_pair`), so it never disturbs other keys, records, or fields. `newvalue` is type-detected: valid JSON is stored as its native type, otherwise as a JSON string. The tool reuses the existing `allowed_tables` access-control gate. Because the write path is dedicated to this tool and only ever touches the `metadata` column, the read-only guarantee enforced by `validate_select_only` on every other tool is untouched. Per user direction and Constitution Principle IV, the tool emits INFO-level structured logs containing all input parameters and the operation result.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastMCP, psycopg (async), structlog, Pydantic  
**Storage**: PostgreSQL + PostGIS; identity column `id` is always `bigint PRIMARY KEY`; target column `metadata` of type `jsonb`  
**Testing**: pytest, pytest-asyncio, FastMCP `Client` (in-process), unittest.mock  
**Target Platform**: Linux/macOS server (MCP stdio server)  
**Project Type**: Single project (MCP server) — existing `src/` + `tests/` layout  
**Performance Goals**: Single-row update; no batch/throughput target. One atomic statement per call.  
**Constraints**: Parameterized SQL only (no string concatenation of values); writes restricted to the `metadata` column via this tool only; all other tools remain read-only.  
**Scale/Scope**: One new tool, one service, one model; exactly 1 record affected per call (id is the primary key).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. MCP Protocol Compliance**: PASS — Tool declared with `@mcp.tool()`; typed signature yields a complete input JSON Schema. Errors raised as `ValueError` surface as MCP `ToolError` (consistent with existing tools). No proprietary protocol extensions.
- **II. Type Safety**: PASS — Full type annotations on every new function; a Pydantic `UpsertResult` model for the boundary; value parsing returns typed JSON. No new `Any` except where mirroring existing tool wrappers (`conn: object`), matching established pattern.
- **III. Syntactic Simplicity**: PASS — One service function (build pair → atomic UPDATE → inspect rowcount), one thin tool wrapper (validate → access check → call service → log). Nesting ≤ 3; no metaclass/decorator magic.
- **IV. Log Coverage**: PASS — INFO log on invocation with all parameters and detected value type; INFO log on result (status + rows affected); DEBUG log of the SQL template + elapsed time; ERROR log with full context on failure. Reuses existing structlog setup and the `ToolLoggingMiddleware` envelope.
- **Technical Constraints (SQL safety)**: PASS — Values passed as bound parameters; identifiers (schema/table) composed via `psycopg.sql.Identifier` after allow-list validation. No string concatenation of untrusted input.

**Result**: All gates pass. No entries required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-upsert-metadata/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── upsert_metadata.md   # Tool contract (inputs, outputs, errors)
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
src/
├── server.py                 # + register @mcp.tool() upsert_metadata
├── models/
│   └── upsert.py             # NEW: UpsertResult Pydantic model
├── services/
│   ├── upsert.py             # NEW: atomic UPDATE + column checks
│   ├── access_control.py     # reused (is_table_allowed)
│   └── fieldmeaning.py       # reused (check_table_exists)
└── tools/
    └── upsert.py             # NEW: upsert_metadata_tool (validate, access, parse, log)

tests/
├── unit/
│   ├── test_upsert_value_parsing.py   # NEW: JSON auto-detection (FR-012)
│   └── test_upsert_service.py         # NEW: SQL build + rowcount handling (mocked conn)
└── functional/
    └── test_upsert_tool.py            # NEW: end-to-end via MCP client + DB
```

**Structure Decision**: Single-project MCP server. The feature follows the established three-layer split already used by `query`, `fieldmeaning`, and `schema`: a `tools/` wrapper (input validation, access control, logging, response shaping), a `services/` module (database access), and a `models/` Pydantic result type. The tool is registered in `src/server.py` exactly like the existing four tools.

## Complexity Tracking

> No constitution violations. Section intentionally empty.
