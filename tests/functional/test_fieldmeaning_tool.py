"""Functional tests for the fieldmeaning MCP tool."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError


pytestmark = pytest.mark.functional


@pytest.mark.usefixtures("test_tables")
class TestFieldmeaningTool:
    """Tests for the 'fieldmeaning' MCP tool via MCP client."""

    async def test_returns_columns_with_descriptions(self, mcp_client):
        result = await mcp_client.call_tool(
            "fieldmeaning", {"table_name": "test_parcels"}
        )
        text = result.content[0].text
        assert "gid" in text
        assert "Unique parcel identifier" in text
        assert "Human-readable parcel name" in text

    async def test_null_description_for_uncommented_column(self, mcp_client):
        result = await mcp_client.call_tool(
            "fieldmeaning", {"table_name": "test_parcels"}
        )
        text = result.content[0].text
        assert "area_sqm" in text
        # area_sqm has no comment, so description should be null
        assert "null" in text.lower() or "None" in text

    async def test_nonexistent_table_error(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "fieldmeaning", {"table_name": "nonexistent_xyz"}
            )

    async def test_restricted_table_denied(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "fieldmeaning", {"table_name": "test_restricted"}
            )

    async def test_schema_qualified_name_rejected(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "fieldmeaning", {"table_name": "public.test_parcels"}
            )
