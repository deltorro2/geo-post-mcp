# geo-post-mcp Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-23

## Active Technologies
- Python 3.11+ + pytest, pytest-asyncio, mcp (MCP Python SDK client), unittest.mock (005-test-coverage)
- PostgreSQL with PostGIS (test database, same config as production) (005-test-coverage)
- Python 3.11+ + FastMCP (MCP Python SDK), structlog, psycopg (001-enhanced-logging)
- PostgreSQL with PostGIS (no changes) (001-enhanced-logging)
- Python 3.11+ + FastMCP (MCP Python SDK), psycopg, structlog (002-query-output-format)
- PostgreSQL with PostGIS (EPSG:4326 / WGS84) (002-query-output-format)

- Python 3.11+ + FastMCP (MCP Python SDK), psycopg (async PostgreSQL driver), Pydantic (004-fieldmeaning-tool)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 002-query-output-format: Added Python 3.11+ + FastMCP (MCP Python SDK), psycopg, structlog
- 001-enhanced-logging: Added Python 3.11+ + FastMCP (MCP Python SDK), structlog, psycopg
- 005-test-coverage: Added Python 3.11+ + pytest, pytest-asyncio, mcp (MCP Python SDK client), unittest.mock


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
