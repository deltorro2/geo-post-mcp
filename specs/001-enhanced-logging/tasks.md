# Tasks: Enhanced Logging

**Input**: Design documents from `/specs/001-enhanced-logging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the middleware package structure needed for the new logging middleware.

- [x] T001 Create middleware package with `src/middleware/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the core truncation utility and stdlib-to-structlog bridge that all user stories depend on.

- [x] T002 [P] Implement `_truncate(value, max_len)` helper function in `src/middleware/logging.py` that truncates string values to a given length and appends a truncation indicator. This is used by both INFO (200-char) and DEBUG (2000-char) logging.
- [x] T003 [P] Update `setup_logging()` in `src/config/logging.py` to configure a `structlog.stdlib.ProcessorFormatter` on the root logger handler, replacing the current `logging.basicConfig(format="%(message)s")`. This routes all stdlib log records (including `mcp.*` and `fastmcp.*` loggers) through structlog's processor chain so they get `timestamp` and `event_level` fields in JSON format.

**Checkpoint**: Foundation ready — truncation utility and stdlib bridge in place.

---

## Phase 3: User Story 1 — Structured Tool Call Logging (Priority: P1)

**Goal**: Every MCP tool invocation logs the exact tool name and all parameters at INFO level. Tool completion logs success/failure with key metrics.

**Independent Test**: Invoke any of the 4 MCP tools and verify the log output contains a `tool_call_started` entry with tool name and parameters, and a `tool_call_completed` entry with status and metrics.

### Implementation for User Story 1

- [x] T004 [US1] Create the `ToolLoggingMiddleware` class in `src/middleware/logging.py` as a FastMCP `Middleware` subclass. Override `on_call_tool()` to: (a) log `tool_call_started` at INFO level with tool name and all parameter names/values truncated to 200 chars, (b) call `call_next(context)`, (c) log `tool_call_completed` at INFO level with tool name, `status="success"`, `duration_ms`, and result metrics. Use structlog for all logging.
- [x] T005 [US1] Add error handling in `on_call_tool()` in `src/middleware/logging.py`: wrap `call_next()` in try/except, log `tool_call_error` at ERROR level with tool name, parameters, exception type, exception message, and `duration_ms`. Re-raise the exception after logging.
- [x] T006 [US1] Register the `ToolLoggingMiddleware` in `src/server.py` by calling `mcp.add_middleware(ToolLoggingMiddleware())` after creating the FastMCP instance.
- [x] T007 [US1] Remove redundant `logger.info("tool_invoked")` calls from `src/tools/query.py` (line 75: `query_tool_invoked`), `src/tools/schema.py` (lines 24, 26, 56, 58: `list_tables_tool_invoked`, `list_tables_result`, `describe_table_tool_invoked`, `describe_table_result`), and `src/tools/fieldmeaning.py` (lines 52, 56-60: `fieldmeaning_tool_invoked`, `fieldmeaning_result`). These are now handled centrally by the middleware.

**Checkpoint**: All 4 tools produce `tool_call_started` and `tool_call_completed` INFO log entries with tool name, parameters, and metrics.

---

## Phase 4: User Story 2 — Request/Response Content in Debug Mode (Priority: P2)

**Goal**: When log level is DEBUG, the full request content and response content are logged, enabling operators to reconstruct complete tool interactions from logs alone.

**Independent Test**: Set `log_level` to `"DEBUG"` in settings, invoke a tool, and verify `tool_call_request_detail` and `tool_call_response_detail` entries appear with full parameter values and serialized response content.

### Implementation for User Story 2

- [x] T008 [US2] Add DEBUG-level request logging in `on_call_tool()` in `src/middleware/logging.py`: before calling `call_next()`, log `tool_call_request_detail` at DEBUG level with tool name and full untruncated parameter values.
- [x] T009 [US2] Add DEBUG-level response logging in `on_call_tool()` in `src/middleware/logging.py`: after `call_next()` returns, serialize the result using `pydantic_core.to_json(result, fallback=str)`, truncate to 2,000 characters, and log `tool_call_response_detail` at DEBUG level with tool name, `response_content`, and `response_truncated` boolean.

**Checkpoint**: With `log_level: "DEBUG"`, full request and response content appears in logs. With `log_level: "INFO"`, only summary entries appear.

---

## Phase 5: User Story 3 — Consistent Log Entry Format (Priority: P3)

**Goal**: All log entries — both application-generated and framework-generated (e.g., "Processing request of type CallToolRequest") — include a timestamp and log level in consistent JSON format.

**Independent Test**: Start the server, invoke a tool, and verify every line in the log output is valid JSON containing `timestamp` and `event_level` fields, including MCP SDK framework messages.

### Implementation for User Story 3

- [x] T010 [US3] Verify and adjust the stdlib bridge in `src/config/logging.py` (from T003) to ensure that `mcp.server.lowlevel.server` logger messages pass through structlog processors. Test by checking that "Processing request of type CallToolRequest" entries in the log contain `timestamp` and `event_level` JSON fields. Fix any logger propagation or handler issues if framework messages bypass the bridge.

**Checkpoint**: All log output lines are consistently formatted JSON with timestamps and log levels.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, cleanup, and validation across all stories.

- [x] T011 [P] Add unit tests for the `ToolLoggingMiddleware` in `tests/unit/test_logging_middleware.py`: test INFO-level logging with tool name and truncated params, test ERROR-level logging on tool failure, test DEBUG-level request/response logging, test that response content is capped at 2,000 chars, test that no sensitive data (password) appears in logs.
- [x] T012 [P] Add unit tests for the stdlib-to-structlog bridge in `tests/unit/test_logging.py`: test that a stdlib logger record is formatted as JSON with `timestamp` and `event_level` fields.
- [x] T013 Verify existing tests still pass by running `python -m pytest tests/ -v` and run `mypy --strict src/middleware/` to confirm type safety. Fix any regressions or type errors.
- [x] T014 Run quickstart.md validation: start server with DEBUG level, invoke each of the 4 tools, verify log output matches the examples in `specs/001-enhanced-logging/quickstart.md`.
- [x] T015 [P] Add log assertion tests in `tests/functional/test_logging_integration.py`: using the existing `mcp_client` fixture, invoke each of the 4 tools while capturing log output, and assert that (a) `tool_call_started` entries contain the tool name and parameters, (b) `tool_call_completed` entries contain status and metrics, (c) `tool_call_error` entries appear when invoking a restricted table. This satisfies the constitution requirement that "Logging MUST be verified in integration tests."

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — core middleware implementation
- **US2 (Phase 4)**: Depends on Phase 3 — extends the middleware with DEBUG logging
- **US3 (Phase 5)**: Depends on Phase 2 — verifies the stdlib bridge from T003
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2). No dependency on other stories.
- **User Story 2 (P2)**: Depends on User Story 1 (extends the same middleware `on_call_tool` method).
- **User Story 3 (P3)**: Depends on Foundational (Phase 2) only. Can run in parallel with US1/US2.

### Parallel Opportunities

- T002 and T003 (Foundational) can run in parallel (different files)
- T010 (US3) can start as soon as Phase 2 completes, in parallel with US1/US2
- T011 and T012 (Polish) can run in parallel (different test files)

---

## Parallel Example: Foundational Phase

```bash
# Launch foundational tasks together (different files):
Task: "Implement _truncate helper in src/middleware/logging.py"
Task: "Update setup_logging stdlib bridge in src/config/logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002, T003)
3. Complete Phase 3: User Story 1 (T004–T007)
4. **STOP and VALIDATE**: Invoke all 4 tools, verify INFO-level tool name + params in logs
5. This alone delivers the most-requested feature

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → INFO-level tool call visibility (MVP)
3. Add User Story 2 → DEBUG-level full request/response content
4. Add User Story 3 → Consistent formatting for all log sources
5. Polish → Tests, regression check, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 extends the middleware created in US1 (same file), so it must follow US1
- US3 can proceed independently once the stdlib bridge (T003) is in place
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
