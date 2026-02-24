# Quickstart: Field Meaning Tool

## Prerequisites

- Python 3.11+
- PostgreSQL server with PostGIS extension
- A database with tables that have column comments set via
  `COMMENT ON COLUMN`
- `geo-post-mcp-settings.json` configured with database
  connection details and allowed tables list

## Setup

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Set database password (if required):
   ```bash
   export POSTGISMCPPASS="your_password"
   ```

3. Ensure `geo-post-mcp-settings.json` exists with the target
   table in the allowed list:
   ```json
   {
     "host": "localhost",
     "port": 5432,
     "user": "postgres",
     "schema": "public",
     "allowed_tables": ["parcels", "buildings"]
   }
   ```

## Usage

### Via MCP Client

Call the `fieldmeaning` tool with a table name:

```json
{
  "name": "fieldmeaning",
  "arguments": {
    "table_name": "parcels"
  }
}
```

### Expected Response

```json
{
  "table": "parcels",
  "schema": "public",
  "columns": [
    {
      "column_name": "gid",
      "data_type": "integer",
      "ordinal_position": 1,
      "description": "Unique parcel identifier"
    },
    {
      "column_name": "geom",
      "data_type": "USER-DEFINED",
      "ordinal_position": 2,
      "description": "Parcel boundary geometry"
    }
  ]
}
```

## Verification Steps

1. Start the MCP server.
2. Call `fieldmeaning` with an allowed table name.
3. Verify all columns are returned with correct data types.
4. Verify columns with `COMMENT ON COLUMN` show their
   description text.
5. Verify columns without comments show `null` for description.
6. Call `fieldmeaning` with a disallowed table — expect error.
7. Call `fieldmeaning` with a nonexistent table — expect error.
8. Call `fieldmeaning` with `"public.parcels"` — expect
   rejection (schema-qualified name).
