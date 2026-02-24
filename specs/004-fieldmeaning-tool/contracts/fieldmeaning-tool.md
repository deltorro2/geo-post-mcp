# MCP Tool Contract: fieldmeaning

**Protocol**: MCP (Model Context Protocol)
**Transport**: Streamable HTTP
**Direction**: Client → Server

## Tool Definition

**Name**: `fieldmeaning`
**Description**: Returns the meaning of each field (column) in
a database table, based on schema comments.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "table_name": {
      "type": "string",
      "description": "Bare table name (not schema-qualified). Resolved against the configured schema."
    }
  },
  "required": ["table_name"],
  "additionalProperties": false
}
```

### Success Response

MCP text content containing JSON with the following structure:

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
    },
    {
      "column_name": "area_sqm",
      "data_type": "double precision",
      "ordinal_position": 3,
      "description": null
    }
  ]
}
```

### Error Responses

| Condition                    | MCP Error | Message                                      |
|------------------------------|-----------|----------------------------------------------|
| Table not in allowed list    | Tool error | "Table '{name}' is not in the allowed tables list" |
| Table does not exist         | Tool error | "Table '{name}' not found in schema '{schema}'" |
| Schema-qualified name given  | Tool error | "Only bare table names accepted (no dot/schema prefix)" |
| Database connection failure  | Tool error | "Database connection error: {details}"       |
