"""TypeSafe client wrapper. All Jev calls go through here."""

from __future__ import annotations

import os
from typing import Any

import yaml  # type: ignore[import-untyped]


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load tunable thresholds. Keeps magic numbers out of code.

    Missing, unreadable, or malformed files yield ``{}`` so callers fall
    back to compiled defaults instead of crashing at import/request time.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data: Any = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def get_jev_model(config: dict[str, Any] | None = None) -> str:
    """Return configured Jev model name, defaulting to ``jev-latest``."""
    cfg = config or {}
    jev_cfg: Any = cfg.get("jev", {})
    if isinstance(jev_cfg, dict):
        model: Any = jev_cfg.get("model", "jev-latest")
        if isinstance(model, str) and model:
            return model
    return "jev-latest"


def require_api_key() -> str:
    """Return TYPESAFE_API_KEY or raise with helpful message."""
    key = os.environ.get("TYPESAFE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "TYPESAFE_API_KEY is not set. Copy .env.example and "
            "create a key at https://console.typesafe.ai/keys"
        )
    return key


def build_system_one_request(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """Build payload shape shared by triage/memory/verify (testable offline)."""
    return {"state": state, "questions": questions}
