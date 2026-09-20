"""Test isolation: the API gate reads PULSEDESK_API_KEY from the environment.

CI/dev shells may export a real key, which would flip every TestClient call
into 401s. Default tests to dev-mode (open); auth tests opt in explicitly
via monkeypatch.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _dev_mode_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove PULSEDESK_API_KEY unless the test sets it itself."""
    monkeypatch.delenv("PULSEDESK_API_KEY", raising=False)
