"""Tests for Agent A core triage (offline, no API key required)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from backend.handlers import builtins as _builtins  # noqa: F401
from backend.main import app, dispatch
from backend.registry import HANDLERS
from backend.schemas import Customer, Route, Sender, Ticket, TriageAction, TriageResult
from backend.triage import (
    build_triage_questions,
    build_triage_state,
    compose_triage,
    triage_offline,
)

_BACKTICK_PATH = re.compile(r"`[a-z_]+(?:\.[a-z_]+)+`")


def _ticket() -> Ticket:
    """Build a minimal ticket for tests.

    Returns:
        Ticket with a duplicate-charge billing message.
    """
    return Ticket(
        subject="Charged twice",
        message="I was charged twice, please refund the duplicate.",
        sender=Sender(display_name="Priya", email="priya@acmecorp.com"),
    )


def _customer() -> Customer:
    """Build a minimal customer for tests.

    Returns:
        Default enterprise customer.
    """
    return Customer(plan="enterprise", open_orders=("INV-2041",))


def test_spam_composite_math() -> None:
    """Spam risk equals 0.45*cred + 0.30*mismatch + 0.25*reward."""
    result = compose_triage(
        route_choice="billing",
        route_conf=0.95,
        spam_parts={
            "requests_credentials": 1.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.5,
        frustration=0.0,
        needs_memory=0.0,
        refund=1.0,
        config={},
    )
    assert result.spam_risk == 0.45
    assert result.action == TriageAction.HUMAN_REVIEW  # 0.45 in uncertain band

    full = compose_triage(
        route_choice="billing",
        route_conf=0.95,
        spam_parts={
            "requests_credentials": 1.0,
            "sender_identity_mismatch": 1.0,
            "unexpected_reward": 1.0,
        },
        urgency=0.5,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert full.spam_risk == 1.0

    partial = compose_triage(
        route_choice="billing",
        route_conf=0.95,
        spam_parts={
            "requests_credentials": 0.5,
            "sender_identity_mismatch": 0.5,
            "unexpected_reward": 0.5,
        },
        urgency=0.5,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert partial.spam_risk == 0.5


def test_confidence_gate_low_conf_routes_to_human() -> None:
    """Route confidence below 0.75 forces human_review even with zero spam."""
    result = compose_triage(
        route_choice="billing",
        route_conf=0.5,
        spam_parts={
            "requests_credentials": 0.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.2,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert result.action == TriageAction.HUMAN_REVIEW

    confident = compose_triage(
        route_choice="billing",
        route_conf=0.95,
        spam_parts={
            "requests_credentials": 0.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.2,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert confident.action == TriageAction.AUTO_ROUTE
    assert confident.route is Route.BILLING


def test_quarantine_threshold() -> None:
    """Spam risk at/above 0.6 quarantines; uncertain band gets human review."""
    quarantined = triage_offline(
        _ticket(),
        _customer(),
        {
            "route": "other",
            "route_confidence": 0.95,
            "requests_credentials": 1.0,
            "sender_identity_mismatch": 1.0,
            "unexpected_reward": 0.0,
        },
    )
    assert quarantined.spam_risk == 0.75
    assert quarantined.action == TriageAction.QUARANTINE_SPAM

    borderline = triage_offline(
        _ticket(),
        _customer(),
        {
            "route": "other",
            "route_confidence": 0.95,
            "requests_credentials": 1.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
    )
    assert borderline.action == TriageAction.HUMAN_REVIEW


def test_backtick_paths_present_in_instructions() -> None:
    """Every triage question instruction references state via backtick paths."""
    questions = build_triage_questions()
    assert set(questions) == {
        "route",
        "needs_memory",
        "requests_credentials",
        "sender_identity_mismatch",
        "unexpected_reward",
        "refund_requested",
        "pii_detected",
        "urgency",
        "frustration",
    }
    for name, question in questions.items():
        instructions = question.instructions
        assert isinstance(instructions, str), f"{name} instructions must be text"
        assert _BACKTICK_PATH.search(instructions), f"{name} missing backtick path"
    state = build_triage_state(_ticket(), _customer())
    assert set(state) == {"ticket", "customer", "policy"}


def test_builtins_dispatch_covers_all_routes() -> None:
    """Each route dispatches through the registry to its named handler."""
    assert set(HANDLERS) == {"it_access", "bug_report", "billing", "hr_policy", "other"}
    cases: dict[str, Route] = {
        "it_access": Route.IT_ACCESS,
        "bug_report": Route.BUG_REPORT,
        "billing": Route.BILLING,
        "hr_policy": Route.HR_POLICY,
        "other": Route.OTHER,
    }
    for handler_name, route in cases.items():
        triage = TriageResult(
            route=route,
            route_confidence=0.95,
            spam_risk=0.0,
            urgency=0.5,
            frustration=0.0,
            needs_memory=0.0,
            refund_requested=0.0,
            action=TriageAction.AUTO_ROUTE,
        )
        owners = [h for h in HANDLERS.values() if h.can_handle(triage)]
        assert [h.name for h in owners] == [handler_name]
        result = dispatch(_ticket(), triage)
        assert result.handler == handler_name
        assert result.ticket_subject == "Charged twice"


def test_endpoints_offline() -> None:
    """POST /v1/triage and /v1/ingest work without an API key."""
    client = TestClient(app)
    assert client.get("/healthz").json() == {"status": "ok"}
    payload: dict[str, Any] = {
        "ticket": {
            "subject": "Charged twice",
            "message": "Please refund the duplicate charge.",
            "sender": {"display_name": "Priya", "email": "priya@acmecorp.com"},
        },
        "customer": {"plan": "enterprise", "open_orders": []},
    }
    triage_resp = client.post("/v1/triage", json=payload)
    assert triage_resp.status_code == 200
    assert triage_resp.json()["action"] == "human_review"  # midpoint mock conf 0.5
    ingest_resp = client.post("/v1/ingest", json=payload)
    assert ingest_resp.status_code == 200
    body = ingest_resp.json()
    assert body["triage"]["route"] == "other"
    assert body["handler"]["handler"] == "other"


def test_golden_tickets_file_valid() -> None:
    """Golden eval file has 12 well-formed tickets with expected outcomes."""
    path = Path(__file__).resolve().parent.parent / "evals" / "golden-tickets.json"
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, list) and len(raw) == 14
    routes = {entry["expected_route"] for entry in raw}
    assert {"billing", "it_access", "bug_report", "other"} <= routes
    for entry in raw:
        Ticket(
            subject=entry["ticket"]["subject"],
            message=entry["ticket"]["message"],
            sender=Sender(**entry["ticket"]["sender"]),
        )
        assert entry["expect_action"] in {"auto_route", "human_review", "quarantine_spam"}


def test_other_route_always_reviewed() -> None:
    """Catch-all route has no owning team: confident 'other' still reviews."""
    from backend.triage import compose_triage

    result = compose_triage(
        route_choice="other",
        route_conf=1.0,
        spam_parts={
            "requests_credentials": 0.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.1,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert result.action == TriageAction.HUMAN_REVIEW
    assert "no owning team" in result.reason


def test_empty_message_reviews_via_other_backstop() -> None:
    """Vacuous input must never auto-route, even at high confidence."""
    from backend.triage import compose_triage

    result = compose_triage(
        route_choice="other",
        route_conf=0.99,
        spam_parts={
            "requests_credentials": 0.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.0,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.0,
        config={},
    )
    assert result.action == TriageAction.HUMAN_REVIEW


def test_quarantine_wins_over_attacker_refund() -> None:
    """High spam quarantines even when refund_requested is maxed by injection text."""
    from backend.triage import compose_triage

    result = compose_triage(
        route_choice="billing",
        route_conf=0.9,
        spam_parts={
            "requests_credentials": 1.0,
            "sender_identity_mismatch": 1.0,
            "unexpected_reward": 1.0,
        },
        urgency=0.5,
        frustration=0.0,
        needs_memory=0.0,
        refund=0.99,
        config={},
    )
    assert result.action == TriageAction.QUARANTINE_SPAM


def test_spam_band_edges_are_exclusive() -> None:
    """Exactly 0.40/0.60 are not 'uncertain': 0.40 falls to the confidence gate."""
    from backend.triage import compose_triage

    def at(spam: float) -> TriageResult:
        return compose_triage(
            route_choice="billing",
            route_conf=0.9,
            spam_parts={
                "requests_credentials": spam,
                "sender_identity_mismatch": 0.0,
                "unexpected_reward": 0.0,
            },
            urgency=0.2,
            frustration=0.0,
            needs_memory=0.0,
            refund=0.0,
            config={
                "spam": {
                    "weights": {
                        "requests_credentials": 1.0,
                        "sender_identity_mismatch": 0.0,
                        "unexpected_reward": 0.0,
                    }
                }
            },
        )

    assert at(0.40).action == TriageAction.AUTO_ROUTE
    assert at(0.45).action == TriageAction.HUMAN_REVIEW
    assert at(0.60).action == TriageAction.QUARANTINE_SPAM


def test_pii_signal_flows_through() -> None:
    """Mock pii_detected reaches the result for downstream consumers."""
    from backend.triage import triage_offline

    result = triage_offline(_ticket(), _customer(), {"pii_detected": 0.9})
    assert result.pii_detected == 0.9
