"""Unit tests for the ToolLoggingMiddleware."""

from __future__ import annotations

import io
import json
import logging
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog

from src.middleware.logging import (
    INFO_PARAM_MAX_LEN,
    DEBUG_RESPONSE_MAX_LEN,
    ToolLoggingMiddleware,
    _truncate,
    _truncate_params,
)


# --- _truncate tests ---


class TestTruncate:
    def test_short_string_unchanged(self) -> None:
        assert _truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self) -> None:
        assert _truncate("hello", 5) == "hello"

    def test_long_string_truncated(self) -> None:
        result = _truncate("a" * 300, 200)
        assert len(result) == 200 + len("...[truncated]")
        assert result.endswith("...[truncated]")

    def test_empty_string(self) -> None:
        assert _truncate("", 10) == ""


class TestTruncateParams:
    def test_none_params(self) -> None:
        assert _truncate_params(None, 200) == {}

    def test_empty_params(self) -> None:
        assert _truncate_params({}, 200) == {}

    def test_short_values_unchanged(self) -> None:
        result = _truncate_params({"key": "val"}, 200)
        assert result == {"key": "val"}

    def test_long_values_truncated(self) -> None:
        result = _truncate_params({"sql": "x" * 300}, 200)
        assert result["sql"].endswith("...[truncated]")

    def test_non_string_values_converted(self) -> None:
        result = _truncate_params({"limit": 100}, 200)
        assert result["limit"] == "100"


# --- ToolLoggingMiddleware tests ---


def _make_context(tool_name: str, arguments: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock MiddlewareContext for tool calls."""
    ctx = MagicMock()
    ctx.message.name = tool_name
    ctx.message.arguments = arguments
    return ctx


def _parse_log_entries(output: str) -> list[dict[str, Any]]:
    """Parse JSON log entries from captured output."""
    entries = []
    for line in output.strip().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _setup_structlog_to_buffer(buf: io.StringIO) -> None:
    """Configure structlog to write to a StringIO buffer."""
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=buf),
        cache_logger_on_first_use=False,
    )


@pytest.mark.asyncio
async def test_info_logging_with_tool_name_and_params() -> None:
    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    mw = ToolLoggingMiddleware()
    ctx = _make_context("query", {"sql": "SELECT 1", "row_limit": 10})
    call_next = AsyncMock(return_value={"columns": [], "rows": [], "row_count": 0})

    await mw.on_call_tool(ctx, call_next)

    entries = _parse_log_entries(buf.getvalue())
    started = [e for e in entries if e.get("event") == "tool_call_started"]
    assert len(started) == 1
    assert started[0]["tool_name"] == "query"
    assert "sql" in started[0]["parameters"]
    assert "row_limit" in started[0]["parameters"]

    completed = [e for e in entries if e.get("event") == "tool_call_completed"]
    assert len(completed) == 1
    assert completed[0]["tool_name"] == "query"
    assert completed[0]["status"] == "success"
    assert "duration_ms" in completed[0]


@pytest.mark.asyncio
async def test_info_params_truncated_to_200() -> None:
    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    mw = ToolLoggingMiddleware()
    long_sql = "x" * 500
    ctx = _make_context("query", {"sql": long_sql})
    call_next = AsyncMock(return_value={})

    await mw.on_call_tool(ctx, call_next)

    entries = _parse_log_entries(buf.getvalue())
    started = [e for e in entries if e.get("event") == "tool_call_started"]
    assert len(started) == 1
    assert len(started[0]["parameters"]["sql"]) <= INFO_PARAM_MAX_LEN + len("...[truncated]")


@pytest.mark.asyncio
async def test_error_logging_on_tool_failure() -> None:
    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    mw = ToolLoggingMiddleware()
    ctx = _make_context("query", {"sql": "SELECT * FROM bad"})
    call_next = AsyncMock(side_effect=ValueError("Access denied"))

    with pytest.raises(ValueError, match="Access denied"):
        await mw.on_call_tool(ctx, call_next)

    entries = _parse_log_entries(buf.getvalue())
    errors = [e for e in entries if e.get("event") == "tool_call_error"]
    assert len(errors) == 1
    assert errors[0]["tool_name"] == "query"
    assert errors[0]["error_type"] == "ValueError"
    assert "Access denied" in errors[0]["error_message"]
    assert "duration_ms" in errors[0]


@pytest.mark.asyncio
async def test_debug_request_has_full_params() -> None:
    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    mw = ToolLoggingMiddleware()
    long_sql = "y" * 500
    ctx = _make_context("query", {"sql": long_sql})
    call_next = AsyncMock(return_value={})

    await mw.on_call_tool(ctx, call_next)

    entries = _parse_log_entries(buf.getvalue())
    detail = [e for e in entries if e.get("event") == "tool_call_request_detail"]
    assert len(detail) == 1
    assert detail[0]["parameters"]["sql"] == long_sql  # full, untruncated


@pytest.mark.asyncio
async def test_debug_response_capped_at_2000() -> None:
    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    mw = ToolLoggingMiddleware()
    ctx = _make_context("query", {"sql": "SELECT 1"})
    large_result = {"data": "z" * 5000}
    call_next = AsyncMock(return_value=large_result)

    await mw.on_call_tool(ctx, call_next)

    entries = _parse_log_entries(buf.getvalue())
    resp = [e for e in entries if e.get("event") == "tool_call_response_detail"]
    assert len(resp) == 1
    assert resp[0]["response_truncated"] is True
    assert len(resp[0]["response_content"]) <= DEBUG_RESPONSE_MAX_LEN + len("...[truncated]")


@pytest.mark.asyncio
async def test_no_password_in_logs() -> None:
    """Ensure database password never appears in tool call logs."""
    import os

    buf = io.StringIO()
    _setup_structlog_to_buffer(buf)

    password = os.environ.get("POSTGISMCPPASS", "test_secret_pw")
    mw = ToolLoggingMiddleware()
    ctx = _make_context("query", {"sql": "SELECT 1", "row_limit": 10})
    call_next = AsyncMock(return_value={"row_count": 0})

    await mw.on_call_tool(ctx, call_next)

    log_content = buf.getvalue()
    assert password not in log_content
