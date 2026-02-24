"""Root conftest — shared markers and auto-marker fixtures."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-apply unit/functional markers based on test file location."""
    for item in items:
        test_path = str(item.fspath)
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/functional/" in test_path:
            item.add_marker(pytest.mark.functional)
