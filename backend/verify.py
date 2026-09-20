"""Response verification: Choice + Noul questions, pure compose, live call.

A draft reply is checked against retrieved evidence. :func:`compose_verify`
maps the Jev answers to a :class:`VerifyResult` purely offline so the
verdict policy is unit-testable without an API key.
"""

from __future__ import annotations

from typing import Any, Literal

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul

from .jev_client import (
    build_system_one_request,
    get_jev_model,
    load_config,
    require_api_key,
)
from .schemas import VerifyResult

SUPPORT_LABELS: tuple[str, str, str] = ("supported", "contradicted", "unsupported")

_DEFAULT_NEEDS_REVIEW = 0.5


def _review_threshold(config: dict[str, Any] | None) -> float:
    """Read the needs-review threshold from config with a fallback."""
    section = (config or {}).get("verify", {})
    raw = (
        section.get("needs_review_threshold", _DEFAULT_NEEDS_REVIEW)
        if isinstance(section, dict)
        else _DEFAULT_NEEDS_REVIEW
    )
    return float(raw) if isinstance(raw, (int, float)) else _DEFAULT_NEEDS_REVIEW


def _clamp(value: float) -> float:
    """Clamp a probability to [0, 1]."""
    return max(0.0, min(1.0, value))


def build_verify_questions(reply: str, evidence: str) -> dict[str, Choice | Noul]:
    """Build verification questions for a draft reply against evidence.

    Returns a ``support`` :class:`Choice` (supported / contradicted /
    unsupported) plus a ``needs_review`` :class:`Noul` gate. Instructions
    reference state via backtick paths (`` `reply` ``, `` `evidence` ``).
    """
    _ = (reply, evidence)  # carried in state; referenced by path below.
    return {
        "support": Choice(
            instructions="Given the evidence at `evidence`, how does the draft reply at `reply` hold up?",  # noqa: E501
            criteria={
                "supported": "The reply at `reply` is fully supported by `evidence`.",
                "contradicted": "The reply at `reply` is contradicted by `evidence`.",
                "unsupported": "The reply at `reply` is neither supported nor contradicted.",
            },
        ),
        "needs_review": Noul(
            instructions="Does the reply at `reply` need human review before sending?",
        ),
    }


def compose_verify(
    choice: str,
    needs_review: float,
    probabilities: dict[str, float] | None = None,
    needs_review_threshold: float = _DEFAULT_NEEDS_REVIEW,
) -> VerifyResult:
    """Map Jev answers to a verdict. Pure offline function.

    Confident ``supported`` stays supported, confident ``unsupported``
    stays unsupported; contradictions, high ``needs_review``, and unknown
    labels all route to ``needs_review`` for a human.
    """
    probs = probabilities or {}
    needs_review = _clamp(needs_review)
    confidence = _clamp(float(probs.get(choice, 0.0))) if probs else _clamp(1.0 - needs_review)
    supported = _clamp(float(probs.get("supported", 1.0 if choice == "supported" else 0.0)))
    verdict: Literal["supported", "needs_review", "unsupported"]
    if choice == "supported" and needs_review < needs_review_threshold:
        verdict = "supported"
    elif choice == "unsupported" and needs_review < needs_review_threshold:
        verdict = "unsupported"
    else:
        verdict = "needs_review"
    return VerifyResult(supported=supported, confidence=confidence, verdict=verdict)


async def verify_live(
    reply: str,
    evidence: str,
    config_path: str = "config.yaml",
) -> VerifyResult:
    """Verify ``reply`` against ``evidence`` via live System One call."""
    config = load_config(config_path)
    api_key = require_api_key()  # clear error when the key is missing.
    questions = build_verify_questions(reply, evidence)
    state: dict[str, Any] = {"reply": reply, "evidence": evidence}
    request = build_system_one_request(state, questions)
    async with AsyncTypeSafeClient(api_key=api_key, model=get_jev_model(config)) as client:
        response = await client.system_one(request["state"], questions)
    choice_answer = response.choices["support"]
    return compose_verify(
        choice_answer.choice,
        response.nouls["needs_review"].noul,
        dict(choice_answer.probabilities),
        _review_threshold(config),
    )
