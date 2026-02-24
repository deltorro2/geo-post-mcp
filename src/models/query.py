"""Pydantic models for query results."""

from __future__ import annotations

from pydantic import BaseModel


class QueryResult(BaseModel):
    """Structured result from a SQL query execution."""

    columns: list[str]
    rows: list[list[object]]
    row_count: int
    truncated: bool
