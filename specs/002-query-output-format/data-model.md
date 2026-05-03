# Data Model: Query Output Format

**Feature**: 002-query-output-format  
**Date**: 2026-04-30

## Overview

This feature does not modify the database schema. It adds a new output serialization format for existing query results. The data model describes the two response structures.

## Text Response (existing, unchanged)

```json
{
  "columns": ["gid", "name", "area_sqm", "geom"],
  "rows": [
    [1, "Park A", 5000.0, "0101000020E6100000..."],
    [2, "Park B", 3000.0, "0101000020E6100000..."]
  ],
  "row_count": 2,
  "truncated": false,
  "message": "Results truncated to 1000 rows."
}
```

Fields:
- `columns`: list of column name strings
- `rows`: list of row arrays (values match column order)
- `row_count`: integer count of returned rows
- `truncated`: boolean (only present when true)
- `message`: string (only present when truncated)

## GeoJSON Response (new)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
      },
      "properties": {
        "gid": 1,
        "name": "Park A",
        "area_sqm": 5000.0
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
      },
      "properties": {
        "gid": 2,
        "name": "Park B",
        "area_sqm": 3000.0
      }
    }
  ],
  "row_count": 2,
  "truncated": false,
  "message": "Results truncated to 1000 rows."
}
```

Fields:
- `type`: always `"FeatureCollection"` (RFC 7946)
- `features`: array of Feature objects
  - `type`: always `"Feature"`
  - `geometry`: GeoJSON geometry object from the `geom` column (or `null` if geometry is NULL)
  - `properties`: dict of all non-geom column values as key-value pairs
- `row_count`: integer count of returned rows (foreign member)
- `truncated`: boolean (foreign member, only present when true)
- `message`: string (foreign member, only present when truncated)

## CRS

All geometry coordinates are in WGS84 (EPSG:4326), which is the mandatory CRS per RFC 7946 and expected by Leaflet.
