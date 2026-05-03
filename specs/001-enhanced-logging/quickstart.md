# Quickstart: Enhanced Logging

**Feature**: 001-enhanced-logging  
**Date**: 2026-04-30

## What Changed

The server now provides detailed, structured logging for every MCP tool call. All log entries (including framework messages) use consistent JSON format with timestamps and log levels.

## Configuration

No new configuration options. Use the existing `log_level` setting in `geo-post-mcp-settings.json`:

```json
{
  "log_level": "INFO"
}
```

Set to `"DEBUG"` for full request/response content logging.

## Log Output Examples

### INFO Level (default)

Tool invocation:
```json
{"event": "tool_call_started", "event_level": "info", "timestamp": "2026-04-30T12:00:00Z", "tool_name": "query", "parameters": {"sql": "SELECT * FROM parcels ORDER BY gid", "row_limit": 1000}}
```

Tool completion:
```json
{"event": "tool_call_completed", "event_level": "info", "timestamp": "2026-04-30T12:00:01Z", "tool_name": "query", "status": "success", "duration_ms": 45.2, "row_count": 25}
```

### DEBUG Level

Full request detail:
```json
{"event": "tool_call_request_detail", "event_level": "debug", "timestamp": "2026-04-30T12:00:00Z", "tool_name": "query", "parameters": {"sql": "SELECT * FROM parcels WHERE ST_DWithin(geom, ST_GeomFromText('POINT(34.05 -118.25)', 4326), 0.01) ORDER BY gid", "row_limit": 1000}}
```

Full response detail (capped at 2,000 chars):
```json
{"event": "tool_call_response_detail", "event_level": "debug", "timestamp": "2026-04-30T12:00:01Z", "tool_name": "query", "response_content": "{\"columns\": [\"gid\", \"name\"], \"rows\": [[1, \"Park A\"]], \"row_count\": 1}", "response_truncated": false}
```

### ERROR Level

```json
{"event": "tool_call_error", "event_level": "error", "timestamp": "2026-04-30T12:00:01Z", "tool_name": "query", "parameters": {"sql": "SELECT * FROM nonexistent"}, "error_type": "ValueError", "error_message": "Access denied: table 'nonexistent' is not in the allowed tables list.", "duration_ms": 1.2}
```

## Verifying the Setup

1. Start the server with `log_level: "DEBUG"` in settings
2. Invoke any tool via an MCP client
3. Check the log output for entries with `tool_name` field
4. Verify framework messages (e.g., "Processing request of type CallToolRequest") now include `timestamp` and `event_level` fields
