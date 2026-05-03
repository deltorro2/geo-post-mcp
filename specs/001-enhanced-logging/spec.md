# Feature Specification: Enhanced Logging

**Feature Branch**: `001-enhanced-logging`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: User description: "I want my project to be logged much better. Add more prints of DEBUG and INFO level. I want to know not only the fact of request or response, but their content as well (in debug mode). Also add timestamps and level for prints like Processing request of type CallToolRequest / Dispatching request of type CallToolRequest which appears in my log. All calls of specific tool should have the exact tool name and parameters."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured Tool Call Logging (Priority: P1)

As a server operator, I want every MCP tool invocation to log the exact tool name and all parameters it was called with, so I can understand what requests the server is handling and troubleshoot issues.

**Why this priority**: Tool call visibility is the core ask. Without knowing which tool was called and with what arguments, debugging is impossible.

**Independent Test**: Can be tested by invoking any MCP tool (e.g., `query`, `list_tables`, `describe_table`, `fieldmeaning`) and verifying the log output contains the tool name and all input parameters.

**Acceptance Scenarios**:

1. **Given** the server is running at any log level, **When** a tool is invoked (e.g., `query` with `sql="SELECT * FROM parcels"` and `row_limit=100`), **Then** an INFO-level log entry is emitted containing the tool name (`query`) and all parameters (`sql`, `row_limit`) with their values.
2. **Given** the server is running at any log level, **When** the `describe_table` tool is invoked with `table_name="parcels"`, **Then** the log entry includes the tool name and the table name parameter value.
3. **Given** the server is running at any log level, **When** the `fieldmeaning` tool is invoked, **Then** the log entry includes the tool name and the table name parameter.

---

### User Story 2 - Request/Response Content in Debug Mode (Priority: P2)

As a developer debugging an issue, I want to see the full content of incoming requests and outgoing responses when the log level is set to DEBUG, so I can inspect exactly what data is flowing through the server.

**Why this priority**: Content-level visibility is essential for deep debugging but only needed in DEBUG mode to avoid noise in production.

**Independent Test**: Can be tested by setting log level to DEBUG, invoking a tool, and verifying that both the full request payload and the full response payload appear in the log output.

**Acceptance Scenarios**:

1. **Given** the server is running with log level DEBUG, **When** a tool is invoked, **Then** the full request content (tool name, all parameters and their complete values) is logged at DEBUG level.
2. **Given** the server is running with log level DEBUG, **When** a tool returns a response, **Then** the response content (result data) is logged at DEBUG level, capped at 2,000 characters with a truncation note if the content exceeds that limit.
3. **Given** the server is running with log level INFO, **When** a tool is invoked, **Then** the detailed request/response content is NOT logged (only the summary INFO-level entry appears).

---

### User Story 3 - Consistent Log Entry Format (Priority: P3)

As a server operator, I want all log entries to include a timestamp and log level, including framework-generated messages like "Processing request of type CallToolRequest" and "Dispatching request of type CallToolRequest", so I can correlate events chronologically and filter by severity.

**Why this priority**: Consistent formatting across all log sources (application and framework) makes logs parseable and usable in log aggregation tools.

**Independent Test**: Can be tested by starting the server and inspecting all log output lines to verify each one contains a timestamp and log level.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** any log entry is emitted by the application, **Then** it contains a timestamp and a log level indicator.
2. **Given** the server is running, **When** framework-level messages (e.g., "Processing request of type CallToolRequest") are emitted, **Then** they also contain a timestamp and a log level, formatted consistently with application log entries.
3. **Given** the server is running, **When** a tool call completes successfully, **Then** both the invocation log and the result log share a consistent format with timestamps.

---

### Edge Cases

- What happens when a tool call raises an error? The error details (exception type, message) should be logged at ERROR level with the tool name and parameters that caused it.
- What happens when request parameters contain very large values (e.g., a long SQL query)? In DEBUG mode, the full content is logged. In INFO mode, parameter values are truncated to 200 characters.
- What happens when sensitive data appears in parameters? The existing password-masking behavior must be preserved; no database credentials should appear in logs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST log every tool invocation at INFO level with the exact tool name and all input parameter names with values truncated to 200 characters. Full untruncated values are logged at DEBUG level.
- **FR-002**: System MUST log the full request content (all parameters with complete values) at DEBUG level when the configured log level is DEBUG.
- **FR-003**: System MUST log response content (result data) at DEBUG level when the configured log level is DEBUG, capped at 2,000 characters with a truncation note if exceeded.
- **FR-004**: System MUST include a timestamp and log level in every log entry produced by the application.
- **FR-005**: System MUST route framework-generated log messages (from the MCP SDK / FastMCP) through the same logging configuration so they also include timestamps and log levels.
- **FR-006**: System MUST log tool call errors at ERROR level, including the tool name, the parameters that were passed, and the error details.
- **FR-007**: System MUST NOT log sensitive information such as database passwords, regardless of log level.
- **FR-008**: System MUST log tool call completion at INFO level with the tool name, a success/failure indicator, and tool-specific result metrics: `row_count` and `truncated` for `query`; `table_count` for `list_tables`; `column_count` for `describe_table`; `column_count` for `fieldmeaning`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tool invocation produces a log entry containing the tool name and all parameter values, verifiable by invoking each of the four tools and inspecting the log output.
- **SC-002**: In DEBUG mode, the operator can reconstruct the full request and response for any tool call solely from the log output.
- **SC-003**: All log entries (both application and framework-generated) contain a timestamp and log level, with zero unformatted lines in the output.
- **SC-004**: Switching from INFO to DEBUG level increases log detail without requiring any code changes or server restart beyond updating the configuration.
- **SC-005**: No database passwords or other credentials appear in log output at any log level.

## Clarifications

### Session 2026-04-30

- Q: Should INFO-level logs show full or truncated parameter values? → A: Truncated to 200 characters at INFO; full untruncated values at DEBUG.
- Q: Should DEBUG-level response logging have a size cap? → A: Cap at 2,000 characters with a truncation note if exceeded.

## Assumptions

- The existing structured JSON log format (via structlog) will be preserved and extended, not replaced.
- "Timestamps and level" for framework messages means routing FastMCP/MCP SDK logging through the existing structlog pipeline so they get the same JSON format with `timestamp` and `event_level` fields.
- Parameter values logged at INFO level are truncated to 200 characters; DEBUG level logs the full untruncated content.
- The log level is configured via the existing `log_level` setting in the settings file; no new configuration options are needed.
