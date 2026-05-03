"""Functional tests verifying logging integration through MCP tool calls.

Satisfies constitution requirement: "Logging MUST be verified in integration
tests (assert expected log entries are emitted)."
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastmcp.exceptions import ToolError

from src.config.settings import load_settings


pytestmark = pytest.mark.functional


@pytest.fixture(scope="session")
def log_file_path() -> str:
    """Get the log file path from settings."""
    settings = load_settings()
    if not settings.log_file:
        pytest.skip("No log_file configured in settings; cannot assert log entries")
    return settings.log_file


def _read_recent_log_entries(log_file: str, max_lines: int = 50) -> list[dict[str, Any]]:
    """Read the most recent JSON log entries from the log file."""
    entries: list[dict[str, Any]] = []
    try:
        with open(log_file) as f:
            lines = f.readlines()
        for line in lines[-max_lines:]:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        pass
    return entries


def _get_file_position(log_file: str) -> int:
    """Get current end position of log file."""
    try:
        with open(log_file) as f:
            f.seek(0, 2)  # seek to end
            return f.tell()
    except FileNotFoundError:
        return 0


def _read_entries_after(log_file: str, pos: int) -> list[dict[str, Any]]:
    """Read JSON log entries written after the given file position."""
    entries: list[dict[str, Any]] = []
    try:
        with open(log_file) as f:
            f.seek(pos)
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return entries


@pytest.mark.usefixtures("test_tables")
class TestLoggingIntegration:
    """Tests that tool calls produce expected log entries."""

    async def test_query_tool_logs_started_and_completed(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        await mcp_client.call_tool(
            "query", {"sql": "SELECT * FROM test_parcels ORDER BY gid"}
        )
        entries = _read_entries_after(log_file_path, pos)

        started = [e for e in entries if e.get("event") == "tool_call_started"]
        assert any(e.get("tool_name") == "query" for e in started)

        completed = [e for e in entries if e.get("event") == "tool_call_completed"]
        assert any(
            e.get("tool_name") == "query" and e.get("status") == "success"
            for e in completed
        )

    async def test_list_tables_tool_logs_started(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        await mcp_client.call_tool("list_tables", {})
        entries = _read_entries_after(log_file_path, pos)

        started = [e for e in entries if e.get("event") == "tool_call_started"]
        assert any(e.get("tool_name") == "list_tables" for e in started)

    async def test_describe_table_logs_started(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        await mcp_client.call_tool(
            "describe_table", {"table_name": "test_parcels"}
        )
        entries = _read_entries_after(log_file_path, pos)

        started = [e for e in entries if e.get("event") == "tool_call_started"]
        assert any(e.get("tool_name") == "describe_table" for e in started)

    async def test_fieldmeaning_logs_started(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        await mcp_client.call_tool(
            "fieldmeaning", {"table_name": "test_parcels"}
        )
        entries = _read_entries_after(log_file_path, pos)

        started = [e for e in entries if e.get("event") == "tool_call_started"]
        assert any(e.get("tool_name") == "fieldmeaning" for e in started)

    async def test_restricted_table_logs_error(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "query", {"sql": "SELECT * FROM test_restricted"}
            )
        entries = _read_entries_after(log_file_path, pos)

        errors = [e for e in entries if e.get("event") == "tool_call_error"]
        assert any(
            e.get("tool_name") == "query" and "error_type" in e
            for e in errors
        )

    async def test_log_entries_have_timestamp_and_level(
        self, mcp_client: Any, log_file_path: str
    ) -> None:
        pos = _get_file_position(log_file_path)
        await mcp_client.call_tool(
            "query", {"sql": "SELECT * FROM test_parcels LIMIT 1"}
        )
        entries = _read_entries_after(log_file_path, pos)

        tool_entries = [
            e for e in entries
            if e.get("event", "").startswith("tool_call_")
        ]
        assert len(tool_entries) >= 2  # at least started + completed
        for entry in tool_entries:
            assert "timestamp" in entry, f"Missing timestamp in {entry['event']}"
            assert "level" in entry, f"Missing level in {entry['event']}"
