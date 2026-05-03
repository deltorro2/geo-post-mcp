# Quickstart: Query Output Format

**Feature**: 002-query-output-format  
**Date**: 2026-04-30

## What Changed

The `query` tool now accepts an `output_format` parameter with two options:
- `"text"` (default) — existing tabular format with columns and rows
- `"geojson"` — RFC 7946 GeoJSON FeatureCollection, compatible with Leaflet

## Usage Examples

### Text Format (default, unchanged)

```json
{
  "sql": "SELECT gid, name FROM test_parcels ORDER BY gid",
  "row_limit": 100
}
```

Response:
```json
{
  "columns": ["gid", "name"],
  "rows": [[1, "Park A"], [2, "Park B"]],
  "row_count": 2
}
```

### GeoJSON Format (new)

```json
{
  "sql": "SELECT gid, name, geom FROM test_parcels ORDER BY gid",
  "output_format": "geojson"
}
```

Response:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
      "properties": {"gid": 1, "name": "Park A"}
    },
    {
      "type": "Feature",
      "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]},
      "properties": {"gid": 2, "name": "Park B"}
    }
  ],
  "row_count": 2
}
```

### Using GeoJSON with Leaflet

```javascript
// Fetch GeoJSON from MCP query tool response
const geojsonData = response;  // the FeatureCollection from the query tool

// Add directly to Leaflet map
L.geoJSON(geojsonData, {
  onEachFeature: function(feature, layer) {
    layer.bindPopup(feature.properties.name);
  }
}).addTo(map);
```

### Error: GeoJSON Without Geometry Column

```json
{
  "sql": "SELECT gid, name FROM test_parcels",
  "output_format": "geojson"
}
```

Response: Error — "GeoJSON output requires a column named 'geom' in the query results."

### Error: Invalid Format

```json
{
  "sql": "SELECT * FROM test_parcels",
  "output_format": "csv"
}
```

Response: Error — "Invalid output_format 'csv'. Valid options: 'text', 'geojson'."

## Key Notes

- The `geom` column must be included in the SELECT for GeoJSON output
- Geometry is automatically converted from PostGIS format to GeoJSON (no need for `ST_AsGeoJSON()` in SQL)
- All coordinates are in WGS84 (EPSG:4326)
- Rows with NULL geometry appear as Features with `null` geometry
- Row limit truncation metadata is included in the FeatureCollection response
