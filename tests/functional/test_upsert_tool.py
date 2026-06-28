"""Functional tests for the upsert_metadata MCP tool."""

from __future__ import annotations

import json

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.functional


async def _metadata_for(db_connection, schema: str, row_id: int) -> dict:
    """Read back the metadata jsonb for a test_meta row."""
    async with db_connection.cursor() as cur:
        await cur.execute(
            f"SELECT metadata FROM {schema}.test_meta WHERE id = %s", (row_id,)
        )
        row = await cur.fetchone()
    if row is None:
        return {}
    value = row[0]
    if value is None:
        return {}
    return value if isinstance(value, dict) else json.loads(value)


@pytest.mark.usefixtures("test_tables")
class TestUpsertMetadataTool:
    """Tests for the 'upsert_metadata' MCP tool via MCP client."""

    # ----- User Story 1: add a new key -----

    async def test_add_new_key(self, mcp_client, db_connection, test_settings):
        result = await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 1, "newkey": "source", "newvalue": "survey-2026"},
        )
        text = result.content[0].text
        assert "updated" in text

        meta = await _metadata_for(db_connection, test_settings.schema_, 1)
        assert meta["source"] == "survey-2026"
        # Pre-existing keys preserved (FR-004).
        assert meta["existing"] == "kept"

    async def test_typed_value_stored_as_number(
        self, mcp_client, db_connection, test_settings
    ):
        await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 1, "newkey": "year", "newvalue": "2026"},
        )
        meta = await _metadata_for(db_connection, test_settings.schema_, 1)
        assert meta["year"] == 2026
        assert isinstance(meta["year"], int)

    async def test_creates_metadata_when_null(
        self, mcp_client, db_connection, test_settings
    ):
        # Row 2 starts with NULL metadata (FR-005).
        await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 2, "newkey": "k", "newvalue": "v"},
        )
        meta = await _metadata_for(db_connection, test_settings.schema_, 2)
        assert meta == {"k": "v"}

    # ----- User Story 2: replace an existing key -----

    async def test_replace_existing_key_no_duplicate(
        self, mcp_client, db_connection, test_settings
    ):
        await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 1, "newkey": "status", "newvalue": "published"},
        )
        meta = await _metadata_for(db_connection, test_settings.schema_, 1)
        assert meta["status"] == "published"
        # Other keys untouched.
        assert meta["existing"] == "kept"

    # ----- User Story 3: invalid requests -----

    async def test_nonexistent_id_returns_not_found(
        self, mcp_client, db_connection, test_settings
    ):
        result = await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 999999, "newkey": "k", "newvalue": "v"},
        )
        text = result.content[0].text
        assert "not_found" in text
        # No row was created for the missing id.
        meta = await _metadata_for(db_connection, test_settings.schema_, 999999)
        assert meta == {}

    async def test_disallowed_table_denied(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "upsert_metadata",
                {"table_name": "test_restricted", "id": 1, "newkey": "k", "newvalue": "v"},
            )

    async def test_table_without_metadata_column_ineligible(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "upsert_metadata",
                {"table_name": "test_nometa", "id": 1, "newkey": "k", "newvalue": "v"},
            )

    async def test_schema_qualified_name_rejected(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "upsert_metadata",
                {"table_name": "public.test_meta", "id": 1, "newkey": "k", "newvalue": "v"},
            )

    async def test_empty_key_rejected(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "upsert_metadata",
                {"table_name": "test_meta", "id": 1, "newkey": "", "newvalue": "v"},
            )

    # ----- Read-only guarantee preserved (SC-005) -----

    async def test_query_tool_still_rejects_writes(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "query", {"sql": "UPDATE test_meta SET metadata = '{}'"}
            )


def _get_log_pos(log_file: str) -> int:
    try:
        with open(log_file) as f:
            f.seek(0, 2)
            return f.tell()
    except FileNotFoundError:
        return 0


def _read_log_after(log_file: str, pos: int) -> list[dict]:
    entries: list[dict] = []
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


@pytest.fixture(scope="session")
def log_file_path(db_settings) -> str:
    if not db_settings.log_file:
        pytest.skip("No log_file configured in settings; cannot assert log entries")
    return db_settings.log_file


@pytest.mark.usefixtures("test_tables")
class TestUpsertMetadataLogging:
    """Verify logging of parameters and result (constitution Principle IV).

    structlog writes JSON to the configured log file (PrintLoggerFactory), so we
    assert against the file rather than stdlib caplog.
    """

    async def test_success_logs_parameters_and_result(self, mcp_client, log_file_path):
        pos = _get_log_pos(log_file_path)
        await mcp_client.call_tool(
            "upsert_metadata",
            {"table_name": "test_meta", "id": 1, "newkey": "logged", "newvalue": "yes"},
        )
        entries = _read_log_after(log_file_path, pos)
        events = {e.get("event") for e in entries}
        assert "upsert_metadata_requested" in events
        assert "upsert_metadata_completed" in events

        requested = next(e for e in entries if e.get("event") == "upsert_metadata_requested")
        # All parameters are visible in the request log.
        assert requested.get("newkey") == "logged"
        assert requested.get("newvalue") == "yes"
        assert requested.get("id") == 1
        assert requested.get("table") == "test_meta"

        completed = next(e for e in entries if e.get("event") == "upsert_metadata_completed")
        # The result is visible in the completion log.
        assert completed.get("status") == "updated"
        assert completed.get("rows_affected") == 1

    async def test_error_path_is_logged(self, mcp_client, log_file_path):
        pos = _get_log_pos(log_file_path)
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "upsert_metadata",
                {"table_name": "test_restricted", "id": 1, "newkey": "k", "newvalue": "v"},
            )
        entries = _read_log_after(log_file_path, pos)
        errors = [e for e in entries if e.get("event") == "tool_call_error"]
        assert any(
            e.get("tool_name") == "upsert_metadata" and "error_type" in e for e in errors
        )
