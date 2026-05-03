# Research: Enhanced Logging

**Feature**: 001-enhanced-logging  
**Date**: 2026-04-30

## Research Task 1: Framework Log Message Routing

**Question**: How to route MCP SDK/FastMCP log messages through structlog for consistent formatting?

**Decision**: Use `structlog.stdlib.ProcessorFormatter` as a logging formatter attached to Python's root logger handler, replacing the current `logging.basicConfig(format="%(message)s")` configuration.

**Rationale**: The MCP SDK emits "Processing request of type CallToolRequest" and "Dispatching request of type CallToolRequest" via standard Python `logging.getLogger("mcp.server.lowlevel.server")` at lines 727-730 of `mcp/server/lowlevel/server.py`. By configuring a `ProcessorFormatter` on the root logger's handler, all stdlib log records (including from `mcp.*` and `fastmcp.*` loggers) pass through structlog's processor chain, gaining `timestamp` and `event_level` fields in JSON format.

**Alternatives considered**:
- Patching MCP SDK logger directly: Fragile, breaks on SDK updates
- Separate formatting for stdlib logs: Inconsistent output format
- Disabling MCP SDK logs entirely: Loses useful framework context

## Research Task 2: FastMCP Middleware for Tool-Call Logging

**Question**: What is the best hook point for centralized tool-call logging?

**Decision**: Implement a custom `Middleware` subclass overriding `on_call_tool()`. This hook receives a `MiddlewareContext` containing `message.name` (tool name) and `message.arguments` (tool parameters dict), and wraps the `call_next()` call to capture the response.

**Rationale**: FastMCP's middleware system (at `fastmcp/server/middleware/middleware.py`) provides operation-specific hooks including `on_call_tool()`. The `MiddlewareContext` carries all needed metadata: tool name, arguments, timestamp, method string. This is superior to per-tool logging because:
- Single implementation point for all 4 tools
- Access to both request and response in one place
- Consistent error handling with `try/except` around `call_next()`
- No changes needed when new tools are added

**Alternatives considered**:
- Per-tool decorator: Requires modifying each tool function, doesn't catch framework errors
- FastMCP's built-in `LoggingMiddleware`: Close but doesn't extract tool name/arguments at the granularity needed (logs generic method/payload, not tool-specific fields)
- Python `logging` filters: Can't intercept at the tool-call level

## Research Task 3: Sensitive Data Protection

**Question**: How to ensure database passwords never appear in logs?

**Decision**: No additional work needed. The password is loaded via `os.environ.get("POSTGISMCPPASS")` in `get_password()` and passed directly to `psycopg.connect()`. It never appears in tool parameters (which are SQL queries, table names, and row limits). The middleware only logs tool parameters and response data, neither of which contain the password. The existing `test_password_not_in_log_output` unit test validates this.

**Rationale**: Tool parameters are: `sql` (string), `table_name` (string), `row_limit` (int). None carry credentials. The database connection is established separately in `_get_connection()` which doesn't log the password.

**Alternatives considered**: N/A — no action needed.

## Research Task 4: Response Content Extraction

**Question**: How to extract response content from tool results for DEBUG logging?

**Decision**: The `on_call_tool()` middleware hook returns the tool's result (a dict or structured object). Serialize it via `pydantic_core.to_json(result, fallback=str)` (same approach used by FastMCP's built-in `BaseLoggingMiddleware._serialize_payload()`), then truncate to 2,000 characters.

**Rationale**: Tool functions return Python dicts (e.g., `{"columns": [...], "rows": [...], "row_count": N}`). Using `pydantic_core.to_json` handles Pydantic models, dicts, and other types consistently. The 2,000-character cap prevents multi-megabyte log entries from large query results.

**Alternatives considered**:
- `json.dumps()`: Fails on non-serializable types without custom encoder
- `str()`: Less structured, harder to parse
- `repr()`: Verbose, includes type annotations
