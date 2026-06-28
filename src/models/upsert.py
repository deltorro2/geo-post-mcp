"""Pydantic model for the upsert_metadata tool result."""

from __future__ import annotations

from pydantic import BaseModel


class UpsertResult(BaseModel):
    """Structured result from an upsert_metadata operation."""

    table: str
    id: int
    key: str
    status: str
    rows_affected: int
