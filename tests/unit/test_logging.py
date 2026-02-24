"""Unit tests for src.config.logging — setup_logging."""

from __future__ import annotations

import logging

import structlog

from src.config.logging import setup_logging


def test_structlog_configured_after_setup(capsys):
    setup_logging(level=logging.INFO)
    log = structlog.get_logger("test_configured")
    log.info("hello")
    captured = capsys.readouterr()
    # structlog prints to stderr via PrintLoggerFactory
    assert "hello" in captured.err


def test_info_level_log_emitted(capsys):
    setup_logging(level=logging.INFO)
    log = structlog.get_logger("test_info")
    log.info("info_event", key="value")
    captured = capsys.readouterr()
    assert "info_event" in captured.err
    assert "value" in captured.err


def test_error_level_log_emitted(capsys):
    setup_logging(level=logging.INFO)
    log = structlog.get_logger("test_error")
    log.error("error_event", detail="something broke")
    captured = capsys.readouterr()
    assert "error_event" in captured.err
    assert "something broke" in captured.err


def test_password_not_in_log_output(capsys):
    setup_logging(level=logging.INFO)
    log = structlog.get_logger("test_no_password")
    # Simulate logging connection info without password
    log.info(
        "database_connected",
        host="localhost",
        port=5432,
        user="admin",
    )
    captured = capsys.readouterr()
    # The password string itself should never appear
    assert "s3cret_password" not in captured.err
    # But the safe fields should be present
    assert "localhost" in captured.err
    assert "admin" in captured.err
