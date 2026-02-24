"""Unit tests for field meaning validation and models."""

from __future__ import annotations

import pytest

from src.tools.fieldmeaning import validate_table_name
from src.models.fieldmeaning import FieldMeaningEntry, FieldMeaningResponse


class TestValidateTableName:
    """Tests for validate_table_name from src.tools.fieldmeaning."""

    def test_bare_table_name_passes(self):
        # Should not raise
        validate_table_name("parcels")

    def test_schema_qualified_rejected(self):
        with pytest.raises(ValueError, match="Schema-qualified"):
            validate_table_name("public.parcels")

    def test_empty_table_name_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_table_name("")

    def test_table_name_with_dot_rejected(self):
        with pytest.raises(ValueError, match="Schema-qualified"):
            validate_table_name("my.table")


class TestFieldMeaningEntry:
    """Tests for FieldMeaningEntry model."""

    def test_serializes_with_description(self):
        entry = FieldMeaningEntry(
            column_name="geom",
            data_type="USER-DEFINED",
            ordinal_position=1,
            description="Polygon geometry of the parcel boundary",
        )
        data = entry.model_dump()
        assert data["column_name"] == "geom"
        assert data["data_type"] == "USER-DEFINED"
        assert data["ordinal_position"] == 1
        assert data["description"] == "Polygon geometry of the parcel boundary"

    def test_serializes_with_null_description(self):
        entry = FieldMeaningEntry(
            column_name="id",
            data_type="integer",
            ordinal_position=1,
            description=None,
        )
        data = entry.model_dump()
        assert data["description"] is None


class TestFieldMeaningResponse:
    """Tests for FieldMeaningResponse model."""

    def test_serializes_correctly(self):
        entries = [
            FieldMeaningEntry(
                column_name="id",
                data_type="integer",
                ordinal_position=1,
                description="Primary key",
            ),
            FieldMeaningEntry(
                column_name="name",
                data_type="text",
                ordinal_position=2,
                description=None,
            ),
        ]
        response = FieldMeaningResponse(
            table="parcels",
            schema_="public",
            columns=entries,
        )
        data = response.model_dump()
        assert data["table"] == "parcels"
        assert data["schema_"] == "public"
        assert len(data["columns"]) == 2
        assert data["columns"][0]["column_name"] == "id"
        assert data["columns"][1]["description"] is None
