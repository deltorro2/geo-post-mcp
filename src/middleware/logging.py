"""Logging middleware for MCP tool call tracing."""

from __future__ import annotations

import time
from typing import Any

import pydantic_core
import structlog
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

def _get_logger() -> structlog.BoundLogger:
    """Get a structlog logger (avoids caching issues in tests)."""
    return structlog.get_logger(__name__)

INFO_PARAM_MAX_LEN = 200
DEBUG_RESPONSE_MAX_LEN = 2000


def _truncate(value: str, max_len: int) -> str:
    """Truncate a string value to max_len, appending indicator if truncated.

    Args:
        value: String to truncate.
        max_len: Maximum allowed length.

    Returns:
        Original string if within limit, otherwise truncated with '...[truncated]' suffix.
    """
    if len(value) <= max_len:
        return value
    return value[:max_len] + "...[truncated]"


def _truncate_params(params: dict[str, Any] | None, max_len: int) -> dict[str, str]:
    """Truncate all parameter values to max_len for logging.

    Args:
        params: Tool call parameters dict.
        max_len: Maximum length per value.

    Returns:
        Dict with string-ified, truncated values.
    """
    if not params:
        return {}
    return {k: _truncate(str(v), max_len) for k, v in params.items()}


class ToolLoggingMiddleware(Middleware):
    """Middleware that logs MCP tool calls with name, parameters, and results."""

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        """Log tool invocation, completion, and errors."""
        tool_name: str = context.message.name  # type: ignore[union-attr]
        params: dict[str, Any] | None = context.message.arguments  # type: ignore[union-attr]

        truncated_params = _truncate_params(params, INFO_PARAM_MAX_LEN)
        _get_logger().info(
            "tool_call_started",
            tool_name=tool_name,
            parameters=truncated_params,
        )

        # DEBUG: full untruncated parameters
        _get_logger().debug(
            "tool_call_request_detail",
            tool_name=tool_name,
            parameters=params or {},
        )

        start = time.perf_counter()
        try:
            result: Any = await call_next(context)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _get_logger().error(
                "tool_call_error",
                tool_name=tool_name,
                parameters=truncated_params,
                error_type=type(exc).__name__,
                error_message=str(exc),
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        _get_logger().info(
            "tool_call_completed",
            tool_name=tool_name,
            status="success",
            duration_ms=duration_ms,
        )

        # DEBUG: serialized response content
        response_str = pydantic_core.to_json(result, fallback=str).decode()
        response_truncated = len(response_str) > DEBUG_RESPONSE_MAX_LEN
        _get_logger().debug(
            "tool_call_response_detail",
            tool_name=tool_name,
            response_content=_truncate(response_str, DEBUG_RESPONSE_MAX_LEN),
            response_truncated=response_truncated,
        )

        return result
