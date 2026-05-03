# Implementation Plan: Enhanced Logging

**Branch**: `001-enhanced-logging` | **Date**: 2026-04-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-enhanced-logging/spec.md`

## Summary

Enhance the geo-post-mcp server logging to provide full tool-call visibility (tool name + parameters at INFO level, full request/response content at DEBUG level) and ensure consistent timestamp/level formatting across all log sources including FastMCP framework messages. Implementation uses a custom FastMCP middleware for centralized tool-call logging and routes the MCP SDK's standard Python logging through structlog for format consistency.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastMCP (MCP Python SDK), structlog, psycopg  
**Storage**: PostgreSQL with PostGIS (no changes)  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux server (Docker container)  
**Project Type**: MCP server (stdio transport)  
**Performance Goals**: N/A (logging enhancement, no throughput changes)  
**Constraints**: Log entries must remain structured JSON; no new dependencies  
**Scale/Scope**: 4 MCP tools, ~6 source files modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | No changes to tool schemas or MCP protocol behavior |
| II. Type Safety | PASS | Middleware will use typed parameters; Pydantic models unchanged |
| III. Syntactic Simplicity | PASS | Single middleware class; no metaclass magic or deep nesting |
| IV. Log Coverage | PASS | This feature directly implements the constitution's logging requirements |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-enhanced-logging/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal - no data entities)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── config/
│   └── logging.py          # MODIFY: add stdlib logging → structlog bridge
├── server.py               # MODIFY: register middleware, remove per-tool logging
├── tools/
│   ├── query.py            # MODIFY: remove redundant logging (handled by middleware)
│   ├── schema.py           # MODIFY: remove redundant logging (handled by middleware)
│   └── fieldmeaning.py     # MODIFY: remove redundant logging (handled by middleware)
├── services/
│   └── query.py            # KEEP: retain query execution timing log (service-level metric)
└── middleware/
    ├── __init__.py          # NEW: package init
    └── logging.py           # NEW: custom logging middleware

tests/
├── unit/
│   ├── test_logging.py              # MODIFY: add tests for stdlib bridge
│   └── test_logging_middleware.py   # NEW: middleware unit tests
└── functional/
    └── (existing tests unchanged)
```

**Structure Decision**: Existing `src/` layout preserved. New `src/middleware/` package added for the logging middleware, following the existing pattern of `src/config/`, `src/services/`, `src/tools/`.

## Implementation Approach

### Strategy: FastMCP Middleware + Stdlib Bridge

Two complementary changes achieve all requirements:

1. **Custom Logging Middleware** (`src/middleware/logging.py`): A FastMCP `Middleware` subclass that hooks `on_call_tool` to log tool name, parameters, response content, and errors at the appropriate levels. This centralizes all tool-call logging in one place, replacing the scattered `logger.info("tool_invoked")` calls across `src/tools/*.py`.

2. **Stdlib-to-Structlog Bridge** (`src/config/logging.py`): Configure Python's standard `logging` module to route through structlog's processor pipeline. This ensures that MCP SDK messages like "Processing request of type CallToolRequest" (emitted via `logging.getLogger("mcp.server.lowlevel.server")`) get the same JSON format with `timestamp` and `event_level` fields.

### Key Design Decisions

- **Middleware over decorator**: FastMCP's middleware pipeline provides `MiddlewareContext` with tool name, arguments, method, and timestamp — everything needed without modifying each tool function.
- **Centralized over scattered**: Current logging is spread across 4 tool files with inconsistent detail. The middleware replaces all of these with a single, consistent implementation.
- **Truncation helper**: A shared `_truncate(value, max_len)` utility handles the 200-char INFO / 2000-char DEBUG response caps consistently.
- **Structlog bridge**: Use `structlog.stdlib.ProcessorFormatter` to format stdlib log records through structlog's processor chain, giving framework messages the same JSON output.

### Parameter Logging Detail

| Level | Tool Invocation | Response |
|-------|----------------|----------|
| INFO | Tool name + all param names + values (truncated to 200 chars each) | Tool name + success/fail + key metrics (row_count, table_count) |
| DEBUG | Tool name + all param names + full untruncated values | Tool name + response content (capped at 2,000 chars) |
| ERROR | Tool name + all params + exception type + message | N/A (error is the response) |
