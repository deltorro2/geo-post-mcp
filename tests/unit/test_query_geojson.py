"""Unit tests for GeoJSON conversion in query tool."""

from __future__ import annotations

import json
from typing import Any

import pytest

from src.models.query import QueryResult
from src.tools.query import _to_geojson_feature_collection


def _make_result(
    columns: list[str],
    rows: list[list[Any]],
    truncated: bool = False,
) -> QueryResult:
    return QueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
    )


# Helper: simulate the columns/rows that the SQL wrapping produces.
# The wrapped SQL adds __geom_geojson alongside the original geom column.


class TestToGeojsonFeatureCollection:
    def test_valid_feature_collection_structure(self) -> None:
        geojson_str = json.dumps({"type": "Point", "coordinates": [1.0, 2.0]})
        result = _make_result(
            columns=["gid", "name", "geom", "__geom_geojson"],
            rows=[[1, "Park A", "raw_wkb", geojson_str]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) == 1
        assert fc["row_count"] == 1

        feature = fc["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert feature["geometry"]["coordinates"] == [1.0, 2.0]
        assert feature["properties"] == {"gid": 1, "name": "Park A"}

    def test_multiple_rows(self) -> None:
        g1 = json.dumps({"type": "Point", "coordinates": [1.0, 2.0]})
        g2 = json.dumps({"type": "Point", "coordinates": [3.0, 4.0]})
        result = _make_result(
            columns=["gid", "geom", "__geom_geojson"],
            rows=[[1, "wkb1", g1], [2, "wkb2", g2]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert len(fc["features"]) == 2
        assert fc["features"][0]["properties"]["gid"] == 1
        assert fc["features"][1]["properties"]["gid"] == 2

    def test_null_geometry(self) -> None:
        result = _make_result(
            columns=["gid", "geom", "__geom_geojson"],
            rows=[[1, None, None]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert fc["features"][0]["geometry"] is None
        assert fc["features"][0]["properties"] == {"gid": 1}

    def test_no_geom_column_raises_error(self) -> None:
        result = _make_result(
            columns=["gid", "name"],
            rows=[[1, "Park A"]],
        )
        with pytest.raises(ValueError, match="column named 'geom'"):
            _to_geojson_feature_collection(result, row_limit=1000)

    def test_truncation_metadata(self) -> None:
        g = json.dumps({"type": "Point", "coordinates": [0.0, 0.0]})
        result = _make_result(
            columns=["gid", "geom", "__geom_geojson"],
            rows=[[1, "wkb", g]],
            truncated=True,
        )
        fc = _to_geojson_feature_collection(result, row_limit=5)

        assert fc["truncated"] is True
        assert "truncated to 5 rows" in fc["message"]

    def test_no_truncation_metadata_when_not_truncated(self) -> None:
        g = json.dumps({"type": "Point", "coordinates": [0.0, 0.0]})
        result = _make_result(
            columns=["gid", "geom", "__geom_geojson"],
            rows=[[1, "wkb", g]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert "truncated" not in fc
        assert "message" not in fc

    def test_polygon_geometry(self) -> None:
        g = json.dumps({
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        })
        result = _make_result(
            columns=["gid", "name", "geom", "__geom_geojson"],
            rows=[[1, "Zone", "wkb", g]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert fc["features"][0]["geometry"]["type"] == "Polygon"

    def test_geom_excluded_from_properties(self) -> None:
        g = json.dumps({"type": "Point", "coordinates": [0.0, 0.0]})
        result = _make_result(
            columns=["gid", "geom", "__geom_geojson"],
            rows=[[1, "wkb", g]],
        )
        fc = _to_geojson_feature_collection(result, row_limit=1000)

        assert "geom" not in fc["features"][0]["properties"]
        assert "__geom_geojson" not in fc["features"][0]["properties"]
