# Quickstart: Test Coverage

## Prerequisites

- Python 3.11+
- PostgreSQL server with PostGIS extension
- A test database accessible with the credentials in your
  settings file
- `geo-post-mcp-settings.json` configured to point to the
  test database

## Setup

1. Install test dependencies:
   ```bash
   pip install -e ".[test]"
   ```
   This installs pytest, pytest-asyncio, and the MCP client SDK.

2. Configure test database settings in
   `geo-post-mcp-settings.json`:
   ```json
   {
     "host": "localhost",
     "port": 5432,
     "user": "postgres",
     "schema": "public",
     "allowed_tables": ["test_parcels", "test_buildings"]
   }
   ```

3. Set database password (if required):
   ```bash
   export POSTGISMCPPASS="your_test_password"
   ```

## Running Tests

### All tests
```bash
pytest
```

### Unit tests only (no database needed)
```bash
pytest -m unit
```

### Functional tests only (requires database)
```bash
pytest -m functional
```

### With verbose output
```bash
pytest -v
```

## Verification Steps

1. Run `pytest -m unit` — all unit tests pass without a
   running database.
2. Run `pytest -m functional` — all functional tests pass
   with the test database.
3. Run `pytest -m functional` without a database — all
   functional tests are skipped with message "database not
   available."
4. Run `pytest` — both unit and functional tests execute
   together.
5. Verify unit tests complete in under 30 seconds.
6. Verify no test data remains in the database after
   functional tests complete.

## Test Categories

| Category   | Directory          | DB Required | What it tests              |
|------------|--------------------|-------------|----------------------------|
| Unit       | tests/unit/        | No          | Core components in isolation |
| Functional | tests/functional/  | Yes         | MCP tools end-to-end via MCP client |
