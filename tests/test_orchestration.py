"""Agent orchestration framework tests. Offline compose only."""

from __future__ import annotations

from pathlib import Path

from backend.orchestration.executor import WORKER_BRIEFS
from backend.orchestration.router import (
    build_router_questions,
    build_router_state,
    compose_route,
)
from backend.orchestration.schemas import SubTask, WorkerResult
from backend.orchestration.trace import TraceLogger
from backend.orchestration.verifier import (
    build_verify_questions,
    build_verify_state,
    compose_verdict,
)

SUBTASK = SubTask(
    id="s1",
    title="Benchmark triage latency",
    brief="Measure p50/max over 10 live calls.",
    acceptance=("table with p50 and max", "sample size stated"),
)


def test_router_questions_shape() -> None:
    """Router asks worker Choice + context/risk Nouls + difficulty Score."""
    questions = build_router_questions()
    assert set(questions) == {"worker", "needs_context", "risky", "difficulty"}
    state = build_router_state(SUBTASK)
    assert state["subtask"]["id"] == "s1"


def test_compose_route_maps_worker_and_escalation() -> None:
    """Confident routine scout passes clean; risky/low-conf escalates."""
    clean = compose_route("s1", "scout", 0.9, 0.2, 0.1, 0.1, {})
    assert clean.worker == "scout" and not clean.needs_reviewer
    risky = compose_route("s1", "builder", 0.9, 0.2, 0.8, 0.5, {})
    assert risky.needs_reviewer
    unsure = compose_route("s1", "scribe", 0.5, 0.2, 0.1, 0.2, {})
    assert unsure.needs_reviewer


def test_compose_route_unknown_worker_falls_back_to_scout() -> None:
    """Unknown labels fall back to read-only scout, never a writer."""
    routed = compose_route("s1", "superhero", 0.9, 0.0, 0.0, 0.0, {})
    assert routed.worker == "scout"


def test_verdict_gates() -> None:
    """Pass needs all signals; collapse escalates; middle retries."""
    assert compose_verdict("s1", 0.9, 0.9, 0.9, {}).verdict == "pass"
    assert compose_verdict("s1", 0.9, 0.2, 0.9, {}).verdict == "escalate"
    assert compose_verdict("s1", 0.8, 0.6, 0.75, {}).verdict == "retry"


def test_verify_questions_reference_state() -> None:
    """All three checks point at result output and acceptance."""
    result = WorkerResult(subtask_id="s1", worker="scout", output="measured p50=1.2s")
    state = build_verify_state(result, ["table with p50"])
    assert state["acceptance"] == ["table with p50"]
    assert set(build_verify_questions()) == {"meets_criteria", "complete", "honest"}


def test_worker_briefs_cover_all_kinds() -> None:
    """Every routable worker kind has a scoping brief."""
    assert set(WORKER_BRIEFS) == {"scout", "builder", "scribe"}


def test_trace_appends_jsonl(tmp_path: Path) -> None:
    """Trace logger writes one JSON object per event."""
    import json

    logger = TraceLogger(tmp_path / "run.jsonl")
    logger.event("route", "s1", "scout 0.9")
    lines = (tmp_path / "run.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["stage"] == "route"
