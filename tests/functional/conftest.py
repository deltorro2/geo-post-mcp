"""Functional test conftest — DB connection, MCP client, test tables."""

from __future__ import annotations

import psycopg
import pytest
import pytest_asyncio

from src.config.settings import Settings, load_settings, get_password


@pytest.fixture(scope="session")
def db_settings():
    """Load database settings from production config file."""
    try:
        return load_settings()
    except (FileNotFoundError, Exception) as exc:
        pytest.skip(f"Skipping functional tests: {exc}")


@pytest.fixture(scope="session")
def test_settings(db_settings):
    """Settings with test tables added to allowed_tables."""
    test_tables_list = ["test_parcels", "test_buildings"]
    combined = list(set(db_settings.allowed_tables + test_tables_list))
    return Settings(
        host=db_settings.host,
        port=db_settings.port,
        user=db_settings.user,
        dbname=db_settings.dbname,
        schema_=db_settings.schema_,  # Use the configured schema
        allowed_tables=combined,
    )


@pytest.fixture(scope="session")
def _check_db(test_settings):
    """Synchronously verify DB is reachable; skip all if not."""
    import psycopg as pg_sync

    password = get_password()
    try:
        conn = pg_sync.connect(
            host=test_settings.host,
            port=test_settings.port,
            user=test_settings.user,
            password=password,
            dbname=test_settings.dbname,
            autocommit=True,
        )
        conn.close()
    except Exception:
        pytest.skip("Skipping functional tests: database not available")


@pytest_asyncio.fixture
async def db_connection(test_settings, _check_db):
    """Function-scoped async DB connection."""
    password = get_password()
    conn = await psycopg.AsyncConnection.connect(
        host=test_settings.host,
        port=test_settings.port,
        user=test_settings.user,
        password=password,
        dbname=test_settings.dbname,
        autocommit=True,
    )
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def mcp_client(db_connection, test_settings):
    """Function-scoped MCP client with injected settings and connection."""
    from fastmcp import Client
    from src.server import mcp as server, configure

    configure(test_settings, db_connection)

    async with Client(server) as client:
        yield client


@pytest_asyncio.fixture
async def test_tables(db_connection):
    """Create test tables with sample data, drop on teardown."""
    conn = db_connection

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_parcels (
            gid integer PRIMARY KEY,
            name varchar(100),
            area_sqm double precision,
            geom geometry(Polygon, 4326)
        )
    """)
    await conn.execute(
        "COMMENT ON COLUMN test_parcels.gid IS 'Unique parcel identifier'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_parcels.name IS 'Human-readable parcel name'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_parcels.geom IS 'Parcel boundary polygon'"
    )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_buildings (
            bid integer PRIMARY KEY,
            parcel_id integer,
            height_m double precision,
            location geometry(Point, 4326)
        )
    """)
    await conn.execute(
        "COMMENT ON COLUMN test_buildings.bid IS 'Building identifier'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_buildings.parcel_id IS 'Reference to parent parcel'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_buildings.height_m IS 'Building height in meters'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_buildings.location IS 'Building centroid'"
    )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_restricted (
            id integer PRIMARY KEY,
            secret text
        )
    """)
    await conn.execute(
        "COMMENT ON COLUMN test_restricted.id IS 'Restricted data'"
    )
    await conn.execute(
        "COMMENT ON COLUMN test_restricted.secret IS 'Sensitive value'"
    )

    # Insert sample data
    await conn.execute("""
        INSERT INTO test_parcels (gid, name, area_sqm, geom) VALUES
            (1, 'Park A', 5000.0, ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))', 4326)),
            (2, 'Park B', 3000.0, ST_GeomFromText('POLYGON((2 2, 3 2, 3 3, 2 3, 2 2))', 4326))
        ON CONFLICT (gid) DO NOTHING
    """)
    await conn.execute("""
        INSERT INTO test_buildings (bid, parcel_id, height_m, location) VALUES
            (1, 1, 10.5, ST_GeomFromText('POINT(0.5 0.5)', 4326)),
            (2, 2, 20.0, ST_GeomFromText('POINT(2.5 2.5)', 4326))
        ON CONFLICT (bid) DO NOTHING
    """)
    await conn.execute("""
        INSERT INTO test_restricted (id, secret) VALUES
            (1, 'classified')
        ON CONFLICT (id) DO NOTHING
    """)

    yield

    # Teardown
    await conn.execute("DROP TABLE IF EXISTS test_restricted")
    await conn.execute("DROP TABLE IF EXISTS test_buildings")
    await conn.execute("DROP TABLE IF EXISTS test_parcels")
