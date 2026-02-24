"""Unit tests for src.services.database — create_connection."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import psycopg
import pytest

from src.config.settings import Settings, PASSWORD_ENV_VAR
from src.services.database import create_connection


@pytest.fixture
def _settings() -> Settings:
    return Settings(
        host="db.example.com",
        port=5433,
        user="geo_user",
        dbname="geo_db",
        **{"schema": "gis"},
        allowed_tables=["parcels"],
    )


async def test_create_connection_called_with_correct_params(_settings, monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV_VAR, "test_pass")
    mock_conn = AsyncMock()

    with patch(
        "psycopg.AsyncConnection.connect",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ) as mock_connect:
        conn = await create_connection(_settings)

        mock_connect.assert_awaited_once_with(
            host="db.example.com",
            port=5433,
            user="geo_user",
            password="test_pass",
            dbname="geo_db",
            autocommit=True,
        )
        assert conn is mock_conn


async def test_connection_failure_raises_exception(_settings, monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV_VAR, "test_pass")

    with patch(
        "psycopg.AsyncConnection.connect",
        new_callable=AsyncMock,
        side_effect=psycopg.OperationalError("connection refused"),
    ):
        with pytest.raises(psycopg.OperationalError, match="connection refused"):
            await create_connection(_settings)


async def test_connection_parameters_match_settings(_settings, monkeypatch):
    monkeypatch.delenv(PASSWORD_ENV_VAR, raising=False)
    mock_conn = AsyncMock()

    with patch(
        "psycopg.AsyncConnection.connect",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ) as mock_connect:
        await create_connection(_settings)

        call_kwargs = mock_connect.call_args.kwargs
        assert call_kwargs["host"] == _settings.host
        assert call_kwargs["port"] == _settings.port
        assert call_kwargs["user"] == _settings.user
        assert call_kwargs["dbname"] == _settings.dbname
        # No POSTGISMCPPASS set, so password should be empty string
        assert call_kwargs["password"] == ""
