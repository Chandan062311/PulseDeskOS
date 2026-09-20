"""Orchestration contracts. Frozen Pydantic, additive-only like schemas.py."""

from __future__ import annotations

from typing import Literal

from ..schemas import Frozen

WorkerKind = Literal["scout", "builder", "scribe"]
Verdict = Literal["pass", "retry", "escalate"]


class SubTask(Frozen):
    """One unit of supervised work."""

    id: str
    title: str
    brief: str
    acceptance: tuple[str, ...]
    skills: tuple[str, ...] = ()


class RouteDecision(Frozen):
    """Jev routing output for one subtask."""

    subtask_id: str
    worker: WorkerKind
    worker_confidence: float
    needs_context: float
    risky: float
    difficulty: float
    needs_reviewer: bool
    reason: str = ""


class WorkerResult(Frozen):
    """Scoped output from one worker agent."""

    subtask_id: str
    worker: WorkerKind
    output: str


class Verification(Frozen):
    """Jev verdict on one worker result."""

    subtask_id: str
    meets_criteria: float
    complete: float
    honest: float
    verdict: Verdict
    reason: str = ""


class SupervisorTrace(Frozen):
    """One logged supervisor event (JSONL-serializable)."""

    run_id: str
    stage: Literal["route", "execute", "verify", "compose", "escalate"]
    subtask_id: str = ""
    detail: str = ""
