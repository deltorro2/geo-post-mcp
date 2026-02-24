"""Database connection manager for geo-post-mcp server."""

from __future__ import annotations

import structlog
import psycopg

from src.config.settings import Settings, get_password

logger = structlog.get_logger(__name__)


async def create_connection(settings: Settings) -> psycopg.AsyncConnection:
    """Create an async database connection from settings.

    Args:
        settings: Server settings with DB connection params.

    Returns:
        An open async psycopg connection.

    Raises:
        psycopg.OperationalError: If connection fails.
    """
    password = get_password()
    conn = await psycopg.AsyncConnection.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=password,
        dbname=settings.dbname,
        autocommit=True,
    )
    logger.info(
        "database_connected",
        host=settings.host,
        port=settings.port,
        user=settings.user,
    )
    return conn
