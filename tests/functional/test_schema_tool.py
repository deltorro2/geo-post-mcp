"""Functional tests for schema discovery MCP tools."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError


pytestmark = pytest.mark.functional


@pytest.mark.usefixtures("test_tables")
class TestSchemaTools:
    """Tests for list_tables and describe_table MCP tools."""

    async def test_list_tables_returns_allowed(self, mcp_client):
        result = await mcp_client.call_tool("list_tables", {})
        text = result.content[0].text
        assert "test_parcels" in text
        assert "test_buildings" in text

    async def test_list_tables_excludes_restricted(self, mcp_client):
        result = await mcp_client.call_tool("list_tables", {})
        text = result.content[0].text
        assert "test_restricted" not in text

    async def test_describe_table_columns(self, mcp_client):
        result = await mcp_client.call_tool(
            "describe_table", {"table_name": "test_parcels"}
        )
        text = result.content[0].text
        assert "gid" in text
        assert "name" in text
        assert "geom" in text

    async def test_describe_table_spatial_info(self, mcp_client):
        result = await mcp_client.call_tool(
            "describe_table", {"table_name": "test_parcels"}
        )
        text = result.content[0].text
        # Should include geometry type info
        assert "geom" in text

    async def test_describe_nonexistent_table_error(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "describe_table", {"table_name": "nonexistent_xyz"}
            )
