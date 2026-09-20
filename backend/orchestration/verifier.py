"""Jev verification: does a worker result meet its acceptance criteria?

``compose_verdict`` is pure: pass when all signals clear the bar, escalate
when any collapses, retry otherwise (one retry with feedback, then escalate
— enforced by the supervisor, not here).
"""

from __future__ import annotations

from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, Noul

from ..jev_client import get_jev_model, load_config, require_api_key
from .schemas import Verdict, Verification, WorkerResult

_DEFAULT_PASS = 0.70
_DEFAULT_COLLAPSE = 0.40


def _verify_thresholds(config: dict[str, Any] | None) -> tuple[float, float]:
    """Return (pass_threshold, collapse_threshold)."""
    orch = (config or {}).get("agent_orchestration", {})
    if not isinstance(orch, dict):
        orch = {}
    pass_raw = orch.get("verify_pass_threshold", _DEFAULT_PASS)
    collapse = orch.get("verify_collapse_threshold", _DEFAULT_COLLAPSE)
    pass_f = float(pass_raw) if isinstance(pass_raw, (int, float)) else _DEFAULT_PASS
    collapse_f = float(collapse) if isinstance(collapse, (int, float)) else _DEFAULT_COLLAPSE
    return pass_f, collapse_f


def build_verify_state(result: WorkerResult, acceptance: list[str]) -> dict[str, Any]:
    """Build verification state with backtick-addressable fields."""
    return {"result": {"output": result.output}, "acceptance": acceptance}


def build_verify_questions() -> dict[str, Noul]:
    """Three independent checks over the same result."""
    return {
        "meets_criteria": Noul(
            instructions="Does `result.output` satisfy every item in `acceptance`?",
        ),
        "complete": Noul(
            instructions="Is `result.output` complete — no placeholders or missing sections?",
        ),
        "honest": Noul(
            instructions="Is `result.output` honest — real measurements, no invented numbers?",
        ),
    }


def compose_verdict(
    subtask_id: str,
    meets_criteria: float,
    complete: float,
    honest: float,
    config: dict[str, Any] | None = None,
) -> Verification:
    """Compose a verification verdict. Pure offline function."""
    pass_t, collapse_t = _verify_thresholds(config)
    scores = {
        "meets_criteria": max(0.0, min(1.0, float(meets_criteria))),
        "complete": max(0.0, min(1.0, float(complete))),
        "honest": max(0.0, min(1.0, float(honest))),
    }
    if all(v >= pass_t for v in scores.values()):
        verdict: Verdict = "pass"
        reason = f"all signals >= {pass_t:.2f}"
    elif any(v < collapse_t for v in scores.values()):
        verdict = "escalate"
        reason = f"a signal collapsed below {collapse_t:.2f}"
    else:
        verdict = "retry"
        reason = f"mixed signals, retry once with feedback (pass bar {pass_t:.2f})"
    return Verification(subtask_id=subtask_id, reason=reason, verdict=verdict, **scores)


async def verify_live(
    result: WorkerResult, acceptance: list[str], config_path: str = "config.yaml"
) -> Verification:
    """Verify one worker result via live Jev. Needs ``TYPESAFE_API_KEY``."""
    config = load_config(config_path)
    require_api_key()
    state = build_verify_state(result, acceptance)
    questions = build_verify_questions()
    model = get_jev_model(config)
    async with AsyncTypeSafeClient() as client:
        response = await client.system_one(state, questions, model=model)
    return compose_verdict(
        subtask_id=result.subtask_id,
        meets_criteria=response.nouls["meets_criteria"].noul,
        complete=response.nouls["complete"].noul,
        honest=response.nouls["honest"].noul,
        config=config,
    )
