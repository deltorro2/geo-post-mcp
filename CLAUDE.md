# geo-post-mcp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-06-25

## Active Technologies
- Python 3.11+ + FastMCP (MCP Python SDK), psycopg (async PostgreSQL driver), structlog, Pydantic
- PostgreSQL with PostGIS (EPSG:4326 / WGS84)
- Testing: pytest, pytest-asyncio, mcp (MCP Python SDK client), unittest.mock
- Python 3.11+ + FastMCP, psycopg (async), structlog, Pydantic (003-upsert-metadata)
- PostgreSQL + PostGIS; target column `metadata` of type `jsonb` (003-upsert-metadata)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
cd src
pytest
ruff check .
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 003-upsert-metadata: Added Python 3.11+ + FastMCP, psycopg (async), structlog, Pydantic
- 002-query-output-format: Added query output format (text/geojson) — FastMCP, psycopg, structlog
- 001-enhanced-logging: Added structured/content logging + middleware — FastMCP, structlog, psycopg


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
