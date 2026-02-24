"""Functional tests for geospatial query capabilities."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.functional


@pytest.mark.usefixtures("test_tables")
class TestGeoQueryTool:
    """Tests for geospatial queries via the 'query' MCP tool."""

    async def test_st_asgeojson(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {"sql": "SELECT ST_AsGeoJSON(geom) FROM test_parcels ORDER BY gid"},
        )
        text = result.content[0].text
        assert "Polygon" in text

    async def test_st_dwithin(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": (
                    "SELECT name FROM test_parcels "
                    "WHERE ST_DWithin(geom, ST_GeomFromText('POINT(0.5 0.5)', 4326), 1)"
                )
            },
        )
        text = result.content[0].text
        assert "Park A" in text

    async def test_spatial_join_st_contains(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": (
                    "SELECT p.name, b.height_m "
                    "FROM test_parcels p "
                    "JOIN test_buildings b ON ST_Contains(p.geom, b.location) "
                    "ORDER BY p.gid"
                )
            },
        )
        text = result.content[0].text
        assert "Park A" in text

    async def test_st_distance(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": (
                    "SELECT ST_Distance("
                    "  ST_GeomFromText('POINT(0 0)', 4326),"
                    "  ST_GeomFromText('POINT(1 1)', 4326)"
                    ")"
                )
            },
        )
        text = result.content[0].text
        # Distance between (0,0) and (1,1) should be ~1.414
        assert "1.4" in text
