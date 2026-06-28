"""Unit tests for upsert_metadata value type auto-detection (FR-012)."""

from __future__ import annotations

import pytest

from src.tools.upsert import parse_value


@pytest.mark.parametrize(
    ("raw", "expected_value", "expected_type"),
    [
        ("42", 42, "number"),
        ("3.14", 3.14, "number"),
        ("true", True, "boolean"),
        ("false", False, "boolean"),
        ("null", None, "null"),
        ("draft", "draft", "string"),
        ("", "", "string"),
        ('"hi"', "hi", "string"),
        ("[1, 2, 3]", [1, 2, 3], "array"),
        ('{"a": 1}', {"a": 1}, "object"),
    ],
)
def test_parse_value(raw: str, expected_value: object, expected_type: str) -> None:
    value, value_type = parse_value(raw)
    assert value == expected_value
    assert value_type == expected_type


def test_bool_is_not_misclassified_as_number() -> None:
    # bool is a subclass of int; ensure it is labelled "boolean", not "number".
    value, value_type = parse_value("true")
    assert value is True
    assert value_type == "boolean"


def test_non_json_text_falls_back_to_string() -> None:
    value, value_type = parse_value("survey-2026")
    assert value == "survey-2026"
    assert value_type == "string"
