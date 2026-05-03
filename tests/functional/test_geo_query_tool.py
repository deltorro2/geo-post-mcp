"""Functional tests for geospatial query capabilities."""

from __future__ import annotations

import json

import pytest
from fastmcp.exceptions import ToolError


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


@pytest.mark.usefixtures("test_tables")
class TestGeoJsonOutput:
    """Tests for GeoJSON output format."""

    async def test_geojson_polygon_feature_collection(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": "SELECT gid, name, geom FROM test_parcels ORDER BY gid",
                "output_format": "geojson",
            },
        )
        text = result.content[0].text
        fc = json.loads(text)
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) == 2
        assert fc["features"][0]["geometry"]["type"] == "Polygon"
        assert fc["features"][0]["properties"]["name"] == "Park A"
        assert "geom" not in fc["features"][0]["properties"]

    async def test_geojson_point_feature(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": "SELECT bid, height_m, location AS geom FROM test_buildings ORDER BY bid",
                "output_format": "geojson",
            },
        )
        text = result.content[0].text
        fc = json.loads(text)
        assert fc["type"] == "FeatureCollection"
        assert fc["features"][0]["geometry"]["type"] == "Point"
        assert fc["features"][0]["properties"]["height_m"] == 10.5

    async def test_geojson_no_geom_column_error(self, mcp_client):
        with pytest.raises(ToolError, match="geom"):
            await mcp_client.call_tool(
                "query",
                {
                    "sql": "SELECT gid, name FROM test_parcels",
                    "output_format": "geojson",
                },
            )

    async def test_invalid_output_format_error(self, mcp_client):
        with pytest.raises(ToolError, match="Invalid output_format"):
            await mcp_client.call_tool(
                "query",
                {
                    "sql": "SELECT * FROM test_parcels",
                    "output_format": "csv",
                },
            )

    async def test_geojson_with_row_count(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {
                "sql": "SELECT gid, geom FROM test_parcels",
                "output_format": "geojson",
            },
        )
        fc = json.loads(result.content[0].text)
        assert fc["row_count"] == 2

    async def test_text_format_default_unchanged(self, mcp_client):
        result = await mcp_client.call_tool(
            "query",
            {"sql": "SELECT gid, name FROM test_parcels ORDER BY gid"},
        )
        text = result.content[0].text
        assert "columns" in text
        assert "rows" in text
        assert "Park A" in text
