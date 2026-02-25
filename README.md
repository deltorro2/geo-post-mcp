# geo-post-mcp

MCP server that provides an AI assistant interface to PostgreSQL databases with PostGIS support. Enables LLMs to execute SQL SELECT queries, run geospatial queries, discover database schema, and read column descriptions — all through the [Model Context Protocol](https://modelcontextprotocol.io/).

## Features

- **SQL Queries** — Execute any SELECT query (JOINs, CTEs, aggregations, subqueries). Non-SELECT statements are rejected.
- **Geospatial Queries** — Full PostGIS support. Geometry columns returned as GeoJSON.
- **Schema Discovery** — List tables, describe columns with types, nullability, defaults, and spatial metadata (geometry type, SRID).
- **Field Meanings** — Read column comments from the database schema to understand what each field represents.
- **Access Control** — Configurable allowed-tables list restricts which tables can be queried.
- **Structured Logging** — JSON-formatted logs via structlog for every tool invocation.

## MCP Tools

| Tool | Description |
|------|-------------|
| `query` | Execute a SQL SELECT query. Returns columns, rows, and row count. |
| `list_tables` | List all allowed tables with estimated row counts. |
| `describe_table` | Describe columns of a table (types, nullability, spatial metadata). |
| `fieldmeaning` | Get column comments/descriptions for a table. |

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 14+ | Database |
| PostGIS | 3.0+ | Geospatial extension for PostgreSQL |
| pip | latest | Python package manager |

### Automated Setup

Install scripts are provided to install all prerequisites and Python dependencies.

**macOS / Linux:**

```bash
chmod +x install.sh
./install.sh
```

**Windows (PowerShell as Administrator):**

```powershell
.\install.ps1
```

### Manual Installation

1. **Python 3.11+** — https://www.python.org/downloads/
2. **PostgreSQL 14+** — https://www.postgresql.org/download/
3. **PostGIS 3.0+** — https://postgis.net/documentation/getting_started/#installing-postgis
4. **Enable PostGIS** in your database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
5. **Install Python dependencies:**
   ```bash
   pip install -e .
   ```
   With test dependencies:
   ```bash
   pip install -e ".[test]"
   ```

## Configuration

### 1. Settings File

Create `geo-post-mcp-settings.json` in the project root:

```json
{
  "host": "127.0.0.1",
  "port": 5432,
  "user": "postgres",
  "dbname": "my_database",
  "schema": "public",
  "allowed_tables": ["parcels", "buildings", "roads"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `host` | string | Database host |
| `port` | integer | Database port |
| `user` | string | Database user |
| `dbname` | string | Database name |
| `schema` | string | Schema to query (default: `public`) |
| `allowed_tables` | string[] | Tables the server is allowed to access |

### 2. Database Password

Set the password via environment variable (never stored in the settings file):

```bash
export POSTGISMCPPASS="your_password"
```

If not set, defaults to empty string (for passwordless local connections).

## Running the Server

Use `--sett` to specify the path to the settings file. If omitted, the server looks for `geo-post-mcp-settings.json` in the current working directory.

### Streamable HTTP (for remote access)

```bash
fastmcp run src/server.py --transport streamable-http --host 0.0.0.0 --port 8000 -- --sett /path/to/geo-post-mcp-settings.json
```

### stdio (for Claude Desktop and local clients)

```bash
fastmcp run src/server.py -- --sett /path/to/geo-post-mcp-settings.json
```

Without `--sett` (looks in current directory):

```bash
fastmcp run src/server.py
```

## Connecting to Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `/Users/michael/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "geo-post-mcp": {
      "command": "/path/to/bin/fastmcp",
      "args": [
        "run",
        "/absolute/path/to/geo-post-mcp/src/server.py",
        "--",
        "--sett",
        "/absolute/path/to/geo-post-mcp/geo-post-mcp-settings.json"
      ],
      "env": {
        "POSTGISMCPPASS": "your_password"
      }
    }
  }
}
```

Replace paths with your actual locations. Use the full path to `fastmcp` (find it with `which fastmcp`). Restart Claude Desktop after editing.

## Connecting to MCP Inspector

### Local

```bash
fastmcp dev src/server.py
```

This opens the MCP Inspector in your browser at `http://localhost:6274`. You can test all tools interactively.

### Remote

Start the server with HTTP transport on the remote machine:

```bash
POSTGISMCPPASS="your_password" fastmcp run src/server.py \
  --transport streamable-http --host 0.0.0.0 --port 8000
```

Then connect MCP Inspector to `http://<remote-host>:8000/mcp/`.

## Running Tests

### Unit tests (no database needed)

```bash
pytest -m unit
```

### Functional tests (requires database)

```bash
pytest -m functional
```

### All tests

```bash
pytest
```

Functional tests automatically skip with a clear message if the database is not available.

## Project Structure

```
src/
├── config/
│   ├── settings.py          # Settings loader (JSON + env var)
│   └── logging.py           # Structured logging setup
├── models/
│   ├── fieldmeaning.py      # Pydantic models for fieldmeaning tool
│   └── query.py             # QueryResult model
├── services/
│   ├── database.py          # Async database connection
│   ├── sql_validator.py     # SELECT-only enforcement
│   ├── access_control.py    # Allowed tables check
│   ├── fieldmeaning.py      # Column metadata queries
│   ├── schema.py            # Schema discovery queries
│   └── query.py             # Query execution
├── tools/
│   ├── query.py             # query MCP tool
│   ├── schema.py            # list_tables, describe_table MCP tools
│   └── fieldmeaning.py      # fieldmeaning MCP tool
└── server.py                # FastMCP server entrypoint

tests/
├── unit/                    # 48 tests, no DB required
└── functional/              # 22 tests, requires PostgreSQL+PostGIS
```

## License

MIT
