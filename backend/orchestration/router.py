"""Jev routing: which worker kind per subtask, plus risk/context flags.

One live call per subtask: Choice (worker) + Nouls (context, risk) + Score
(difficulty). ``compose_route`` is pure and fully tested offline.
"""

from __future__ import annotations

from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from ..jev_client import get_jev_model, load_config, require_api_key
from .schemas import RouteDecision, SubTask, WorkerKind

_DEFAULT_REVIEW_RISK = 0.60
_DEFAULT_REVIEW_CONF = 0.70


def build_router_state(subtask: SubTask) -> dict[str, Any]:
    """Build router state with backtick-addressable fields."""
    return {
        "subtask": {
            "id": subtask.id,
            "title": subtask.title,
            "brief": subtask.brief,
            "acceptance": list(subtask.acceptance),
            "skills": list(subtask.skills),
        }
    }


def build_router_questions() -> dict[str, Choice | Noul | Score]:
    """Worker Choice + context/risk Nouls + difficulty Score."""
    return {
        "worker": Choice(
            instructions="Which worker kind should own `subtask`?",
            criteria={
                "scout": {
                    "what": "Read-only research, measurement, audit, review.",
                    "not_for": "Writing code or docs.",
                    "examples": ["benchmark latencies", "audit docs vs code"],
                },
                "builder": {
                    "what": "Implementing code changes, fixes, features.",
                    "not_for": "Research-only or docs-only tasks.",
                    "examples": ["fix the race condition", "add the endpoint"],
                },
                "scribe": {
                    "what": "Writing docs, notes, changelogs, reports.",
                    "not_for": "Code changes or live measurement.",
                    "examples": ["write the release notes", "draft the runbook"],
                },
            },
        ),
        "needs_context": Noul(
            instructions="Does `subtask` need prior run context (traces, reports) to do well?",
        ),
        "risky": Noul(
            instructions="Is `subtask` risky: irreversible writes or production data?",
        ),
        "difficulty": Score(
            instructions="How difficult is `subtask`?",
            criteria=["routine procedure", "moderate judgment needed", "hard, novel problem"],
        ),
    }


def _review_thresholds(config: dict[str, Any] | None) -> tuple[float, float]:
    """Return (risk_threshold, confidence_threshold) for reviewer escalation."""
    orch = (config or {}).get("agent_orchestration", {})
    if not isinstance(orch, dict):
        orch = {}
    risk = orch.get("review_risk_threshold", _DEFAULT_REVIEW_RISK)
    conf = orch.get("review_conf_threshold", _DEFAULT_REVIEW_CONF)
    risk_f = float(risk) if isinstance(risk, (int, float)) else _DEFAULT_REVIEW_RISK
    conf_f = float(conf) if isinstance(conf, (int, float)) else _DEFAULT_REVIEW_CONF
    return risk_f, conf_f


def compose_route(
    subtask_id: str,
    worker_choice: str,
    worker_conf: float,
    needs_context: float,
    risky: float,
    difficulty: float,
    config: dict[str, Any] | None = None,
) -> RouteDecision:
    """Compose a routing decision. Pure offline function.

    Unknown worker labels fall back to ``scout`` (read-only = safe default).
    ``needs_reviewer`` fires on high risk or low routing confidence.
    """
    if worker_choice == "scout":
        worker: WorkerKind = "scout"
    elif worker_choice == "builder":
        worker = "builder"
    elif worker_choice == "scribe":
        worker = "scribe"
    else:
        worker = "scout"  # read-only = safe default for unknown labels.
    risk_t, conf_t = _review_thresholds(config)
    needs_reviewer = float(risky) >= risk_t or float(worker_conf) < conf_t
    return RouteDecision(
        subtask_id=subtask_id,
        worker=worker,
        worker_confidence=max(0.0, min(1.0, float(worker_conf))),
        needs_context=max(0.0, min(1.0, float(needs_context))),
        risky=max(0.0, min(1.0, float(risky))),
        difficulty=max(0.0, min(1.0, float(difficulty))),
        needs_reviewer=needs_reviewer,
        reason=f"worker {worker} conf {float(worker_conf):.2f}"
        + ("; reviewer escalated" if needs_reviewer else ""),
    )


async def route_live(subtask: SubTask, config_path: str = "config.yaml") -> RouteDecision:
    """Route one subtask via live Jev. Needs ``TYPESAFE_API_KEY``."""
    config = load_config(config_path)
    require_api_key()
    state = build_router_state(subtask)
    questions = build_router_questions()
    model = get_jev_model(config)
    async with AsyncTypeSafeClient() as client:
        response = await client.system_one(state, questions, model=model)
    worker_answer = response.choices["worker"]
    return compose_route(
        subtask_id=subtask.id,
        worker_choice=worker_answer.choice,
        worker_conf=worker_answer.confidence,
        needs_context=response.nouls["needs_context"].noul,
        risky=response.nouls["risky"].noul,
        difficulty=response.scores["difficulty"].score / 2.0,
        config=config,
    )
