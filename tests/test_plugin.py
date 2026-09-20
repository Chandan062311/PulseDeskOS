"""Plugin packaging tests: manifest, skills, agents, MCP config stay valid."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_plugin_manifest() -> None:
    """Manifest has the identity fields Claude Code requires."""
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "pulsedesk"
    assert manifest["description"].strip() != ""
    assert manifest["version"].strip() != ""


def test_skills_have_frontmatter_descriptions() -> None:
    """Every skill carries a description so the host knows when to invoke it."""
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert {p.name for p in skills} >= {"triage", "orchestrate", "memory"}
    for skill in skills:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---"), skill.name
        frontmatter = text.split("---")[1]
        assert "description:" in frontmatter, skill.name


def test_reviewer_agent_declares_plugin_tools() -> None:
    """Reviewer references fully-qualified plugin MCP tool names."""
    text = (ROOT / "agents" / "reviewer.md").read_text(encoding="utf-8")
    assert "mcp__plugin_pulsedesk_pulsedesk__recall_memory" in text
    assert "mcp__plugin_pulsedesk_pulsedesk__verify_response" in text


def test_plugin_mcp_config() -> None:
    """Plugin-root .mcp.json launches the bundled server via plugin root var."""
    config = json.loads((ROOT / ".mcp.json").read_text())
    server = config["mcpServers"]["pulsedesk"]
    assert "${CLAUDE_PLUGIN_ROOT}" in server["args"][0]
    assert server["args"][0].endswith("backend/mcp_server.py")
