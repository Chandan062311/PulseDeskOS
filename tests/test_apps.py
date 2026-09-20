"""Structure tests for reference apps (apps/research)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESEARCH = REPO_ROOT / "apps" / "research"


def test_research_readme_exists() -> None:
    """apps/research/README.md playbook exists."""
    assert (RESEARCH / "README.md").is_file()


def test_scout_prompt_exists_and_shaped() -> None:
    """Scout prompt exists with $TOPIC placeholder and acceptance section."""
    text = (RESEARCH / "prompts" / "scout.md").read_text(encoding="utf-8")
    assert "$TOPIC" in text
    assert "acceptance" in text.lower()


def test_composer_prompt_exists_and_shaped() -> None:
    """Composer prompt exists with $TOPIC placeholder and acceptance section."""
    text = (RESEARCH / "prompts" / "composer.md").read_text(encoding="utf-8")
    assert "$TOPIC" in text
    assert "acceptance" in text.lower()


def test_research_work_dir_exists() -> None:
    """apps/research/work/ output directory exists."""
    assert (RESEARCH / "work").is_dir()
