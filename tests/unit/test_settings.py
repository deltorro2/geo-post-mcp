"""Unit tests for src.config.settings — Settings model, load_settings, get_password."""

from __future__ import annotations

import json
import logging

import pytest
from pydantic import ValidationError

from src.config.settings import Settings, load_settings, get_password, PASSWORD_ENV_VAR


def _write_settings_json(tmp_path, data: dict) -> str:
    """Helper to write a settings JSON file and return its path."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data))
    return path


class TestLoadSettings:
    """Tests for load_settings()."""

    def test_valid_json_parsed_correctly(self, tmp_path):
        data = {
            "host": "db.example.com",
            "port": 5433,
            "user": "admin",
            "dbname": "testdb",
            "schema": "gis",
            "allowed_tables": ["parcels", "buildings"],
        }
        path = _write_settings_json(tmp_path, data)
        settings = load_settings(path)

        assert settings.host == "db.example.com"
        assert settings.port == 5433
        assert settings.user == "admin"
        assert settings.schema_ == "gis"
        assert settings.allowed_tables == ["parcels", "buildings"]

    def test_missing_file_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_settings(missing)

    def test_missing_required_field_raises_validation_error(self, tmp_path):
        data = {"port": 5432, "user": "admin", "dbname": "testdb"}  # missing host
        path = _write_settings_json(tmp_path, data)
        with pytest.raises(ValidationError):
            load_settings(path)

    def test_malformed_port_raises_validation_error(self, tmp_path):
        data = {"host": "localhost", "port": "not_a_number", "user": "admin", "dbname": "testdb"}
        path = _write_settings_json(tmp_path, data)
        with pytest.raises(ValidationError):
            load_settings(path)

    def test_password_env_var_read(self, monkeypatch):
        monkeypatch.setenv(PASSWORD_ENV_VAR, "s3cret")
        assert get_password() == "s3cret"

    def test_missing_password_defaults_to_empty(self, monkeypatch):
        monkeypatch.delenv(PASSWORD_ENV_VAR, raising=False)
        assert get_password() == ""

    def test_unrecognized_field_logs_warning(self, tmp_path, caplog):
        data = {
            "host": "localhost",
            "port": 5432,
            "user": "admin",
            "dbname": "testdb",
            "unknown_option": True,
        }
        path = _write_settings_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            load_settings(path)
        assert "Unrecognized field in settings file: unknown_option" in caplog.text


class TestSettingsModel:
    """Direct model construction tests."""

    def test_schema_alias(self):
        s = Settings(host="h", port=1, user="u", dbname="db", **{"schema": "myschema"})
        assert s.schema_ == "myschema"

    def test_defaults(self):
        s = Settings(host="h", port=1, user="u", dbname="db")
        assert s.schema_ == "public"
        assert s.allowed_tables == []
