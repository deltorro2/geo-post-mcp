# Data Model: Enhanced Logging

**Feature**: 001-enhanced-logging  
**Date**: 2026-04-30

## Overview

This feature does not introduce new data entities or modify the existing database schema. It enhances the logging output format and content. The "data" produced is log entries (structured JSON), not persisted application data.

## Log Entry Structure

Log entries are structured JSON objects produced by structlog. The enhanced logging adds these event types:

### Tool Invocation Entry (INFO)

Fields emitted when a tool is called:

- `event`: `"tool_call_started"` — event identifier
- `event_level`: `"info"` — log level
- `timestamp`: ISO 8601 — when the call was received
- `tool_name`: string — exact tool name (e.g., `"query"`, `"list_tables"`)
- `parameters`: dict — all input parameter names and values (values truncated to 200 chars)

### Tool Completion Entry (INFO)

Fields emitted when a tool returns successfully:

- `event`: `"tool_call_completed"` — event identifier
- `event_level`: `"info"` — log level
- `timestamp`: ISO 8601
- `tool_name`: string
- `status`: `"success"` or `"error"`
- `duration_ms`: float — execution time in milliseconds
- Tool-specific metrics (e.g., `row_count`, `table_count`, `column_count`)

### Tool Error Entry (ERROR)

Fields emitted when a tool raises an exception:

- `event`: `"tool_call_error"` — event identifier
- `event_level`: `"error"` — log level
- `timestamp`: ISO 8601
- `tool_name`: string
- `parameters`: dict — input parameters for debugging
- `error_type`: string — exception class name
- `error_message`: string — exception message
- `duration_ms`: float

### Debug Request Entry (DEBUG)

Fields emitted at DEBUG level before tool execution:

- `event`: `"tool_call_request_detail"` — event identifier
- `event_level`: `"debug"`
- `timestamp`: ISO 8601
- `tool_name`: string
- `parameters`: dict — full untruncated parameter values

### Debug Response Entry (DEBUG)

Fields emitted at DEBUG level after tool execution:

- `event`: `"tool_call_response_detail"` — event identifier
- `event_level`: `"debug"`
- `timestamp`: ISO 8601
- `tool_name`: string
- `response_content`: string — serialized response (capped at 2,000 chars)
- `response_truncated`: boolean — true if content was truncated
