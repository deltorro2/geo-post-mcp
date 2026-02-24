"""Pydantic models for the fieldmeaning MCP tool."""

from __future__ import annotations

from pydantic import BaseModel


class FieldMeaningEntry(BaseModel):
    """A single column's metadata."""

    column_name: str
    data_type: str
    ordinal_position: int
    description: str | None


class FieldMeaningResponse(BaseModel):
    """Complete fieldmeaning tool response."""

    table: str
    schema_: str
    columns: list[FieldMeaningEntry]

    model_config = {"populate_by_name": True}
