"""Unit tests for src.services.fieldmeaning — check_table_exists, get_field_meanings."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.fieldmeaning import check_table_exists, get_field_meanings
from src.models.fieldmeaning import FieldMeaningEntry


@pytest.fixture
def _cursor_mock():
    """Build a mock connection whose .cursor() returns an async context manager.

    psycopg's conn.cursor() is a *synchronous* call that returns an object
    supporting ``async with``.  We therefore use MagicMock for the connection
    and wire up __aenter__/__aexit__ on the cursor manually.
    """
    cursor = AsyncMock()

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=cursor)
    ctx.__aexit__ = AsyncMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = ctx

    return conn, cursor


async def test_check_table_exists_returns_true(_cursor_mock):
    conn, cursor = _cursor_mock
    cursor.fetchone.return_value = (1,)

    result = await check_table_exists(conn, "public", "parcels")

    assert result is True
    cursor.execute.assert_awaited_once()


async def test_check_table_exists_returns_false(_cursor_mock):
    conn, cursor = _cursor_mock
    cursor.fetchone.return_value = None

    result = await check_table_exists(conn, "public", "nonexistent")

    assert result is False


async def test_get_field_meanings_returns_entries(_cursor_mock):
    conn, cursor = _cursor_mock
    cursor.fetchall.return_value = [
        ("id", "integer", 1, "Primary key"),
        ("geom", "USER-DEFINED", 2, "Geometry column"),
    ]

    entries = await get_field_meanings(conn, "public", "parcels")

    assert len(entries) == 2
    assert all(isinstance(e, FieldMeaningEntry) for e in entries)
    assert entries[0].column_name == "id"
    assert entries[0].description == "Primary key"
    assert entries[1].column_name == "geom"
    assert entries[1].ordinal_position == 2


async def test_get_field_meanings_null_descriptions(_cursor_mock):
    conn, cursor = _cursor_mock
    cursor.fetchall.return_value = [
        ("id", "integer", 1, None),
        ("name", "text", 2, None),
    ]

    entries = await get_field_meanings(conn, "public", "parcels")

    assert entries[0].description is None
    assert entries[1].description is None
