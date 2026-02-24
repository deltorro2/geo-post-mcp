"""Unit tests for src.services.access_control — is_table_allowed."""

from __future__ import annotations

from src.services.access_control import is_table_allowed


def test_table_in_allowed_list(mock_allowed_tables):
    assert is_table_allowed("test_parcels", mock_allowed_tables) is True


def test_table_not_in_list(mock_allowed_tables):
    assert is_table_allowed("secret_table", mock_allowed_tables) is False


def test_empty_allowed_list_rejects_all():
    assert is_table_allowed("parcels", []) is False


def test_case_sensitive_matching(mock_allowed_tables):
    # "Test_Parcels" differs from "test_parcels" in case
    assert is_table_allowed("Test_Parcels", mock_allowed_tables) is False
    assert is_table_allowed("test_parcels", mock_allowed_tables) is True


def test_table_name_with_spaces(mock_allowed_tables):
    assert is_table_allowed("test parcels", mock_allowed_tables) is False
