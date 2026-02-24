"""Unit tests for src.services.sql_validator — validate_select_only."""

from __future__ import annotations

import pytest

from src.services.sql_validator import validate_select_only


class TestSelectAccepted:
    """Statements that should be accepted."""

    def test_simple_select(self):
        validate_select_only("SELECT * FROM parcels")

    def test_select_with_joins_where_group_order(self):
        sql = (
            "SELECT a.id, b.name FROM parcels a "
            "JOIN buildings b ON a.id = b.parcel_id "
            "WHERE a.active = true "
            "GROUP BY a.id, b.name "
            "ORDER BY a.id"
        )
        validate_select_only(sql)

    def test_select_with_cte(self):
        sql = (
            "WITH active AS (SELECT * FROM parcels WHERE active = true) "
            "SELECT * FROM active"
        )
        validate_select_only(sql)

    def test_select_with_subquery(self):
        sql = "SELECT * FROM (SELECT id, name FROM parcels) sub"
        validate_select_only(sql)

    def test_select_with_leading_single_line_comment(self):
        sql = "-- fetch all parcels\nSELECT * FROM parcels"
        validate_select_only(sql)

    def test_select_with_leading_block_comment(self):
        sql = "/* fetch parcels */ SELECT * FROM parcels"
        validate_select_only(sql)

    def test_case_insensitive_select(self):
        validate_select_only("select * from parcels")

    def test_case_insensitive_with(self):
        validate_select_only("with cte as (select 1) select * from cte")


class TestMutationsRejected:
    """Write statements that must be rejected."""

    def test_insert_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("INSERT INTO parcels (name) VALUES ('x')")

    def test_update_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("UPDATE parcels SET name = 'x'")

    def test_delete_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("DELETE FROM parcels")

    def test_drop_table_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("DROP TABLE parcels")

    def test_create_table_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("CREATE TABLE t (id int)")

    def test_alter_table_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("ALTER TABLE parcels ADD COLUMN x int")

    def test_truncate_rejected(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_select_only("TRUNCATE parcels")

    def test_empty_statement_rejected(self):
        with pytest.raises(ValueError, match="Empty SQL"):
            validate_select_only("   ")
