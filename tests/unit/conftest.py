"""Unit test conftest — shared mock fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.config.settings import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Return a valid Settings model with test values."""
    return Settings(
        host="localhost",
        port=5432,
        user="test_user",
        dbname="test_db",
        **{"schema": "public"},
        allowed_tables=["test_parcels", "test_buildings"],
    )


@pytest.fixture
def mock_db_connection() -> AsyncMock:
    """Return an AsyncMock for psycopg connection."""
    conn = AsyncMock()
    conn.closed = False
    return conn


@pytest.fixture
def mock_allowed_tables() -> list[str]:
    """Return a test allowed tables list."""
    return ["test_parcels", "test_buildings"]
