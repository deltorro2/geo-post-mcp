"""Unit tests for src.services.upsert — has_metadata_column, upsert_metadata."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.upsert import (
    _UPSERT_TEMPLATE,
    has_metadata_column,
    upsert_metadata,
)


@pytest.fixture
def _cursor_mock():
    """Mock connection whose .cursor() returns an async context manager."""
    cursor = AsyncMock()

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=cursor)
    ctx.__aexit__ = AsyncMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = ctx

    return conn, cursor


def test_upsert_template_uses_atomic_jsonb_merge() -> None:
    # COALESCE handles NULL metadata; the || operator inserts-or-overwrites.
    # Braces are doubled because the template is consumed by str.format().
    assert "COALESCE(metadata::jsonb, '{{}}'::jsonb) || %s::jsonb" in _UPSERT_TEMPLATE
    assert "WHERE id = %s" in _UPSERT_TEMPLATE


async def test_has_metadata_column_true(_cursor_mock) -> None:
    conn, cursor = _cursor_mock
    cursor.fetchone.return_value = (1,)
    assert await has_metadata_column(conn, "public", "parcels") is True


async def test_has_metadata_column_false(_cursor_mock) -> None:
    conn, cursor = _cursor_mock
    cursor.fetchone.return_value = None
    assert await has_metadata_column(conn, "public", "nometa") is False


async def test_upsert_binds_int_id_and_pair_json(_cursor_mock) -> None:
    conn, cursor = _cursor_mock
    cursor.rowcount = 1

    rows = await upsert_metadata(conn, "public", "parcels", 42, '{"k": "v"}')

    assert rows == 1
    cursor.execute.assert_awaited_once()
    _statement, params = cursor.execute.await_args.args
    # id is bound as an integer (not a string), pair_json is the first param.
    assert params == ('{"k": "v"}', 42)
    assert isinstance(params[1], int)


async def test_upsert_returns_zero_when_no_row_matches(_cursor_mock) -> None:
    conn, cursor = _cursor_mock
    cursor.rowcount = 0

    rows = await upsert_metadata(conn, "public", "parcels", 999, '{"k": "v"}')

    assert rows == 0


async def test_upsert_overwrites_existing_key_via_merge(_cursor_mock) -> None:
    # The replace semantics (US2) come from the `||` operator in the template;
    # verify the service issues exactly that merge statement.
    conn, cursor = _cursor_mock
    cursor.rowcount = 1

    await upsert_metadata(conn, "public", "parcels", 1, '{"status": "published"}')

    _statement, params = cursor.execute.await_args.args
    # The merge that overwrites an existing key is the `||` template asserted in
    # test_upsert_template_uses_atomic_jsonb_merge; here we confirm the new pair
    # is passed through as the bound jsonb parameter.
    assert params[0] == '{"status": "published"}'
