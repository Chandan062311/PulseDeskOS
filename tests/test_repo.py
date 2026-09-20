"""Repo hygiene for publishing: marketplace, secrets, portable docs."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PUBLISHABLE_DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "frontend" / "README.md",
    ROOT / "frontend" / "stitch-prompts.md",
    *sorted((ROOT / "skills").rglob("SKILL.md")),
    *sorted((ROOT / "agents").glob("*.md")),
]


def test_marketplace_manifest() -> None:
    """Marketplace catalog is valid and points at this repo's plugin."""
    manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert manifest["name"]
    assert manifest["owner"]["name"]
    entries = {p["name"]: p for p in manifest["plugins"]}
    assert entries["pulsedesk"]["source"] == "./"


def test_no_absolute_author_paths_in_docs() -> None:
    """Publishable docs carry no /home/... paths (sandbox logs exempt)."""
    offenders = [str(p) for p in PUBLISHABLE_DOCS if re.search(r"/home/[a-z_]+", p.read_text())]
    assert offenders == []


def test_no_live_secrets_in_repo() -> None:
    """Same pattern set as scripts/check-secrets.sh (excluding caches)."""
    pattern = re.compile(
        r"apikey_[A-Za-z0-9_-]{8,}|AQ\.Ab8[A-Za-z0-9_-]{8,}|"
        r"sk-(live|test)[A-Za-z0-9]{8,}|xox[bap]-[A-Za-z0-9-]{8,}"
    )
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {
            ".py",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".tsx",
            ".ts",
            ".sh",
            ".toml",
        }:
            continue
        if any(part in {"node_modules", "dist", ".git"} for part in path.parts):
            continue
        if pattern.search(path.read_text(errors="ignore")):
            hits.append(str(path))
    assert hits == []
