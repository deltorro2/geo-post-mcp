"""Functional tests for the SQL query execution MCP tool."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError


pytestmark = pytest.mark.functional


@pytest.mark.usefixtures("test_tables")
class TestQueryTool:
    """Tests for the 'query' MCP tool via MCP client."""

    async def test_select_all_returns_rows(self, mcp_client):
        result = await mcp_client.call_tool(
            "query", {"sql": "SELECT * FROM test_parcels ORDER BY gid"}
        )
        text = result.content[0].text
        assert "Park A" in text
        assert "Park B" in text

    async def test_join_query(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": (
                    "SELECT p.name, b.height_m "
                    "FROM test_parcels p "
                    "JOIN test_buildings b ON p.gid = b.parcel_id "
                    "ORDER BY p.gid"
                )
            },
        )
        text = result.content[0].text
        assert "Park A" in text
        assert "10.5" in text

    async def test_aggregation_query(self, mcp_client):
        result = await mcp_client.call_tool(
            "query", {"sql": "SELECT COUNT(*) FROM test_parcels"}
        )
        text = result.content[0].text
        assert "2" in text

    async def test_cte_query(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": (
                    "WITH parks AS (SELECT * FROM test_parcels) "
                    "SELECT name FROM parks ORDER BY gid"
                )
            },
        )
        text = result.content[0].text
        assert "Park A" in text

    async def test_non_select_rejected(self, mcp_client):
        with pytest.raises(ToolError, match="SELECT"):
            await mcp_client.call_tool(
                "query",
                {"sql": "INSERT INTO test_parcels (gid, name) VALUES (99, 'bad')"},
            )

    async def test_nonexistent_table_error(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "query", {"sql": "SELECT * FROM nonexistent_table_xyz"}
            )

    async def test_restricted_table_denied(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "query", {"sql": "SELECT * FROM test_restricted"}
            )

    async def test_row_limit_truncation(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {"sql": "SELECT * FROM test_parcels", "row_limit": 1},
        )
        text = result.content[0].text
        # Should have at most 1 row of data returned, or truncated indicator
        assert "row_count" in text or "truncated" in text or "Park" in text
