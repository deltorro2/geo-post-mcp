"""Settings loader for geo-post-mcp server."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SETTINGS_FILE_NAME = "geo-post-mcp-settings.json"
PASSWORD_ENV_VAR = "POSTGISMCPPASS"


class Settings(BaseModel):
    """Database and server configuration loaded from settings file."""

    host: str
    port: int
    user: str
    dbname: str
    schema_: str = Field(alias="schema", default="public")
    allowed_tables: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


def load_settings(settings_path: Path | None = None) -> Settings:
    """Load settings from JSON file and environment variable.

    Args:
        settings_path: Explicit path to settings file.
            If None, looks for SETTINGS_FILE_NAME in current directory.

    Returns:
        Validated Settings model.

    Raises:
        FileNotFoundError: If settings file does not exist.
        ValidationError: If settings file has missing or malformed fields.
    """
    if settings_path is None:
        settings_path = Path(SETTINGS_FILE_NAME)

    if not settings_path.exists():
        raise FileNotFoundError(
            f"Settings file not found: {settings_path.resolve()}. "
            f"Expected file named '{SETTINGS_FILE_NAME}'."
        )

    with open(settings_path) as f:
        raw_data = json.load(f)

    known_fields = {"host", "port", "user", "dbname", "schema", "allowed_tables"}
    extra_fields = set(raw_data.keys()) - known_fields
    for field_name in extra_fields:
        logger.warning("Unrecognized field in settings file: %s", field_name)

    settings = Settings(**raw_data)

    logger.info(
        "Settings loaded: host=%s, port=%d, user=%s, dbname=%s, schema=%s, "
        "allowed_tables=%s",
        settings.host,
        settings.port,
        settings.user,
        settings.dbname,
        settings.schema_,
        settings.allowed_tables,
    )

    return settings


def get_password() -> str:
    """Read database password from environment variable.

    Returns:
        Password string, or empty string if not set.
    """
    return os.environ.get(PASSWORD_ENV_VAR, "")
