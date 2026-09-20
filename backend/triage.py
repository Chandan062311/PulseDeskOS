"""Core triage (Agent A).

Builds the System One state + questions for ticket triage and composes the
:class:`TriageResult` from Jev answers. All decision math lives in
:func:`compose_triage`, a pure function that is fully testable offline.
"""

from __future__ import annotations

from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from .jev_client import get_jev_model, load_config, require_api_key
from .schemas import Customer, Route, Ticket, TriageAction, TriageResult

# Default midpoint answers used by /v1/triage when no API key is present.
# Neutral values on purpose: route confidence 0.5 < 0.75 threshold, so the
# result is human_review rather than a fabricated auto_route.
MID_MOCK_ANSWERS: dict[str, str | float] = {
    "route": "other",
    "route_confidence": 0.5,
    "requests_credentials": 0.0,
    "sender_identity_mismatch": 0.0,
    "unexpected_reward": 0.0,
    "urgency": 0.5,
    "frustration": 0.0,
    "needs_memory": 0.5,
    "refund_requested": 0.0,
    "pii_detected": 0.0,
}

_DEFAULT_ROUTE_THRESHOLD = 0.75
_DEFAULT_QUARANTINE = 0.60
_DEFAULT_UNCERTAIN_LOW = 0.40
_DEFAULT_UNCERTAIN_HIGH = 0.60
_DEFAULT_WEIGHTS: dict[str, float] = {
    "requests_credentials": 0.45,
    "sender_identity_mismatch": 0.30,
    "unexpected_reward": 0.25,
}


def build_triage_state(
    ticket: Ticket, customer: Customer, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the System One state dict for a ticket.

    Args:
        ticket: Incoming support ticket.
        customer: Customer context (plan, open orders).
        config: Optional parsed ``config.yaml`` mapping. Policy thresholds
            in state mirror the live config so retuning changes what Jev
            reasons over — never stale module defaults.

    Returns:
        Dict with ``ticket``/``customer``/``policy`` keys. Nested keys mirror
        the backtick paths referenced in question instructions
        (e.g. ```ticket.message```, ```ticket.sender.email```,
        ```customer.plan```).
    """
    cfg = config or {}
    route_gate = _threshold(cfg, "routing", "topic_confidence_threshold", _DEFAULT_ROUTE_THRESHOLD)
    quarantine_at = _threshold(cfg, "spam", "quarantine_threshold", _DEFAULT_QUARANTINE)
    uncertain_low = _threshold(cfg, "spam", "uncertain_low", _DEFAULT_UNCERTAIN_LOW)
    uncertain_high = _threshold(cfg, "spam", "uncertain_high", _DEFAULT_UNCERTAIN_HIGH)
    return {
        "ticket": {
            "subject": ticket.subject,
            "message": ticket.message,
            "sender": {
                "display_name": ticket.sender.display_name,
                "email": ticket.sender.email,
            },
            "links": [{"text": link.text, "url": link.url} for link in ticket.links],
        },
        "customer": {
            "plan": customer.plan,
            "open_orders": list(customer.open_orders),
        },
        "policy": {
            "route_confidence_threshold": route_gate,
            "quarantine_threshold": quarantine_at,
            "uncertain_band": [uncertain_low, uncertain_high],
            "note": (
                "Quarantine when spam risk is high; request human review when "
                "the route is uncertain or spam risk is borderline; otherwise "
                "auto-route."
            ),
        },
    }


def build_triage_questions() -> dict[str, Choice | Noul | Score]:
    """Build the System One questions for ticket triage.

    Returns:
        Mapping of question name to ``typesafe_sdk`` ``Choice``/``Noul``/
        ``Score`` objects. Every instruction references state via backtick
        paths (e.g. ```ticket.message```) so prompts stay grounded in the
        state built by :func:`build_triage_state`.
    """
    route = Choice(
        instructions=(
            "Classify the support ticket with subject `ticket.subject` and body "
            "`ticket.message` (sender `ticket.sender.email`, plan "
            "`customer.plan`) into exactly one route."
        ),
        criteria={
            "it_access": {
                "what": "Password resets, SSO/VPN login failures, locked accounts, "
                "new-hire access provisioning, MFA enrollment.",
                "not_for": "Application crashes, wrong data, or API error responses.",
                "examples": ["locked out of SSO", "can't connect to VPN", "need access"],
            },
            "bug_report": {
                "what": "Product defects: crashes, 500 errors, broken exports, "
                "wrong calculations, UI regressions.",
                "not_for": "Login/access provisioning or billing disputes.",
                "examples": ["500 errors on checkout", "CSV export truncates rows"],
            },
            "billing": {
                "what": "Charges, invoices, refunds, duplicate charges, plan "
                "changes, proration, payment failures.",
                "not_for": "Technical outages or access requests.",
                "examples": ["charged twice", "need invoice copy", "downgrade plan"],
            },
            "hr_policy": {
                "what": "Leave, benefits, payroll dates, remote-work policy, "
                "onboarding paperwork questions.",
                "not_for": "IT access, product bugs, or billing.",
                "examples": ["parental leave policy", "payroll schedule"],
            },
            "other": {
                "what": "Anything that fits none of the above, including vague, "
                "mixed-topic, or suspicious messages.",
                "not_for": "Clearly matching one of the other routes.",
                "examples": ["need help with my account", "hello?"],
            },
        },
    )
    needs_memory = Noul(
        instructions=(
            "Does answering the ticket at `ticket.message` require prior context "
            "such as past tickets, account history, or docs (`customer.plan`)?"
        ),
        criteria={
            "true": "Needs history, docs, or account-specific context to answer.",
            "false": "Answerable from the message alone.",
        },
    )
    requests_credentials = Noul(
        instructions=(
            "Does the message `ticket.message` (subject `ticket.subject`) ask the "
            "reader to share a password, OTP, token, or other secret?"
        ),
        criteria={
            "true": "Asks for passwords, OTPs, tokens, or secrets.",
            "false": "No credential request of any kind.",
        },
    )
    sender_identity_mismatch = Noul(
        instructions=(
            "Does the sender `ticket.sender.email` (`ticket.sender.display_name`) "
            "look inconsistent with the message `ticket.message`, e.g. an "
            "executive request from a free-mail domain?"
        ),
        criteria={
            "true": "Sender identity looks spoofed or inconsistent with content.",
            "false": "Sender and content are consistent.",
        },
    )
    unexpected_reward = Noul(
        instructions=(
            "Does the message `ticket.message` promise an unexpected reward, "
            "prize, gift card, or payout?"
        ),
        criteria={
            "true": "Promises money, prizes, gift cards, or rewards.",
            "false": "No reward or payout is offered.",
        },
    )
    refund_requested = Noul(
        instructions=(
            "Does the customer explicitly request a refund or charge reversal in "
            "`ticket.message` (subject `ticket.subject`)?"
        ),
        criteria={
            "true": "Explicit refund, reimbursement, or charge-back request.",
            "false": "No refund requested.",
        },
    )
    pii_detected = Noul(
        instructions=(
            "Does `ticket.message` (subject `ticket.subject`) contain sensitive "
            "personal data such as an SSN, card number, API key, or password?"
        ),
        criteria={
            "true": "Contains SSN, card number, secret key, or credential value.",
            "false": "No sensitive personal data present.",
        },
    )
    urgency = Score(
        instructions=(
            "How urgent is the ticket at `ticket.message` (subject "
            "`ticket.subject`, plan `customer.plan`)?"
        ),
        criteria=["can wait", "this week", "today", "outage-blocker"],
    )
    frustration = Score(
        instructions=(
            "How frustrated does the customer sound in `ticket.message` (subject `ticket.subject`)?"
        ),
        criteria=["calm", "annoyed", "angry"],
    )
    return {
        "route": route,
        "needs_memory": needs_memory,
        "requests_credentials": requests_credentials,
        "sender_identity_mismatch": sender_identity_mismatch,
        "unexpected_reward": unexpected_reward,
        "refund_requested": refund_requested,
        "pii_detected": pii_detected,
        "urgency": urgency,
        "frustration": frustration,
    }


def _clamp01(value: float) -> float:
    """Clamp a float into the 0..1 range.

    Args:
        value: Raw value.

    Returns:
        Value clipped to ``[0.0, 1.0]``.
    """
    return max(0.0, min(1.0, value))


def _spam_weights(config: dict[str, Any]) -> dict[str, float]:
    """Read spam weights from config with safe fallbacks.

    Args:
        config: Parsed ``config.yaml`` mapping (may be empty).

    Returns:
        Mapping with ``requests_credentials``/``sender_identity_mismatch``/
        ``unexpected_reward`` weights.
    """
    spam_cfg = config.get("spam", {})
    raw_weights: Any = spam_cfg.get("weights", {}) if isinstance(spam_cfg, dict) else {}
    weights = dict(_DEFAULT_WEIGHTS)
    if isinstance(raw_weights, dict):
        for key in weights:
            raw = raw_weights.get(key)
            if isinstance(raw, (int, float)):
                weights[key] = float(raw)
    return weights


def _threshold(config: dict[str, Any], section: str, key: str, default: float) -> float:
    """Read a numeric threshold from config with a fallback default.

    Args:
        config: Parsed ``config.yaml`` mapping (may be empty).
        section: Top-level config section (e.g. ``"spam"``).
        key: Threshold key inside the section.
        default: Value used when missing or non-numeric.

    Returns:
        Configured threshold or the default.
    """
    section_cfg = config.get(section, {})
    if isinstance(section_cfg, dict):
        raw = section_cfg.get(key)
        if isinstance(raw, (int, float)):
            return float(raw)
    return default


def compose_triage(
    route_choice: str,
    route_conf: float,
    spam_parts: dict[str, float],
    urgency: float,
    frustration: float,
    needs_memory: float,
    refund: float,
    config: dict[str, Any],
    pii_detected: float = 0.0,
) -> TriageResult:
    """Compose a :class:`TriageResult` from Jev (or mock) answers.

    Pure function: no I/O, fully testable offline.

    Args:
        route_choice: Winning route label (e.g. ``"billing"``). Unknown labels
            fall back to ``Route.OTHER``.
        route_conf: Route choice confidence in 0..1.
        spam_parts: Noul probabilities keyed by ``requests_credentials``,
            ``sender_identity_mismatch``, ``unexpected_reward``.
        urgency: Normalized urgency in 0..1.
        frustration: Normalized frustration in 0..1.
        needs_memory: Probability prior context is needed, 0..1.
        refund: Probability a refund was requested, 0..1.
        config: Parsed ``config.yaml`` mapping; missing keys fall back to
            ``spam_risk = 0.45*cred + 0.30*mismatch + 0.25*reward``,
            quarantine at ``>= 0.6``, uncertain band ``0.4-0.6``, and route
            confidence gate at ``< 0.75``.
        pii_detected: Probability the message holds sensitive personal data.

    Returns:
        Final :class:`TriageResult` with ``quarantine_spam`` when spam risk is
        at/above threshold, ``human_review`` when spam risk is in the uncertain
        band or route confidence is below threshold, else ``auto_route``.
    """
    weights = _spam_weights(config)
    cred = _clamp01(float(spam_parts.get("requests_credentials", 0.0)))
    mismatch = _clamp01(float(spam_parts.get("sender_identity_mismatch", 0.0)))
    reward = _clamp01(float(spam_parts.get("unexpected_reward", 0.0)))
    spam_risk = _clamp01(
        weights["requests_credentials"] * cred
        + weights["sender_identity_mismatch"] * mismatch
        + weights["unexpected_reward"] * reward
    )

    quarantine_at = _threshold(config, "spam", "quarantine_threshold", _DEFAULT_QUARANTINE)
    uncertain_low = _threshold(config, "spam", "uncertain_low", _DEFAULT_UNCERTAIN_LOW)
    uncertain_high = _threshold(config, "spam", "uncertain_high", _DEFAULT_UNCERTAIN_HIGH)
    route_gate = _threshold(
        config, "routing", "topic_confidence_threshold", _DEFAULT_ROUTE_THRESHOLD
    )

    route_conf = _clamp01(float(route_conf))
    try:
        route = Route(route_choice)
    except ValueError:
        route = Route.OTHER

    if spam_risk >= quarantine_at:
        action = TriageAction.QUARANTINE_SPAM
        reason = f"spam_risk {spam_risk:.2f} >= quarantine {quarantine_at:.2f}"
    elif uncertain_low < spam_risk < uncertain_high or route_conf < route_gate:
        action = TriageAction.HUMAN_REVIEW
        if uncertain_low < spam_risk < uncertain_high:
            reason = (
                f"spam_risk {spam_risk:.2f} in uncertain band "
                f"({uncertain_low:.2f}-{uncertain_high:.2f})"
            )
        else:
            reason = f"route_conf {route_conf:.2f} < gate {route_gate:.2f}"
    else:
        action = TriageAction.AUTO_ROUTE
        reason = f"route {route.value} conf {route_conf:.2f}, spam {spam_risk:.2f}"

    routing_cfg = config.get("routing", {})
    other_review = (
        routing_cfg.get("other_always_review", True) if isinstance(routing_cfg, dict) else True
    )
    if action is TriageAction.AUTO_ROUTE and route is Route.OTHER and other_review:
        action = TriageAction.HUMAN_REVIEW
        reason = f"route other has no owning team (conf {route_conf:.2f}); review"

    return TriageResult(
        route=route,
        route_confidence=route_conf,
        spam_risk=spam_risk,
        urgency=_clamp01(float(urgency)),
        frustration=_clamp01(float(frustration)),
        needs_memory=_clamp01(float(needs_memory)),
        refund_requested=_clamp01(float(refund)),
        pii_detected=_clamp01(float(pii_detected)),
        action=action,
        reason=reason,
    )


def triage_offline(
    ticket: Ticket,
    customer: Customer,
    mock_answers: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> TriageResult:
    """Triage without an API key using caller-supplied mock answers.

    Args:
        ticket: Incoming support ticket (used for state shape only).
        customer: Customer context (used for state shape only).
        mock_answers: Mock Jev answers. Recognized keys: ``route``,
            ``route_confidence`` (alias ``route_conf``),
            ``requests_credentials``, ``sender_identity_mismatch``,
            ``unexpected_reward``, ``urgency``, ``frustration``,
            ``needs_memory``, ``refund_requested`` (alias ``refund``),
            ``pii_detected``.
            Missing keys fall back to neutral :data:`MID_MOCK_ANSWERS`.
        config: Optional parsed config mapping; defaults mirror
            ``config.yaml`` so tests stay hermetic.

    Returns:
        Composed :class:`TriageResult`.
    """
    _ = build_triage_state(ticket, customer, config)  # Validate shapes even offline.
    merged: dict[str, Any] = dict(MID_MOCK_ANSWERS)
    merged.update(mock_answers)
    route_conf_raw = merged.get("route_confidence", merged.get("route_conf", 0.5))
    refund_raw = merged.get("refund_requested", merged.get("refund", 0.0))
    spam_parts = {
        "requests_credentials": float(merged.get("requests_credentials", 0.0)),
        "sender_identity_mismatch": float(merged.get("sender_identity_mismatch", 0.0)),
        "unexpected_reward": float(merged.get("unexpected_reward", 0.0)),
    }
    return compose_triage(
        route_choice=str(merged.get("route", "other")),
        route_conf=float(route_conf_raw),
        spam_parts=spam_parts,
        urgency=float(merged.get("urgency", 0.5)),
        frustration=float(merged.get("frustration", 0.0)),
        needs_memory=float(merged.get("needs_memory", 0.0)),
        refund=float(refund_raw),
        config=config if config is not None else {},
        pii_detected=float(merged.get("pii_detected", 0.0)),
    )


async def triage_live(
    ticket: Ticket,
    customer: Customer,
    config_path: str = "config.yaml",
) -> TriageResult:
    """Triage via the live TypeSafe System One API.

    Args:
        ticket: Incoming support ticket.
        customer: Customer context.
        config_path: Path to ``config.yaml`` for thresholds + model name.

    Returns:
        Composed :class:`TriageResult` from live Jev answers.

    Raises:
        RuntimeError: If ``TYPESAFE_API_KEY`` is not set.
    """
    config = load_config(config_path)
    require_api_key()
    state = build_triage_state(ticket, customer, config)
    questions = build_triage_questions()
    model = get_jev_model(config)
    async with AsyncTypeSafeClient() as client:
        response = await client.system_one(state, questions, model=model)

    route_answer = response.choices["route"]
    spam_parts = {
        "requests_credentials": response.nouls["requests_credentials"].noul,
        "sender_identity_mismatch": response.nouls["sender_identity_mismatch"].noul,
        "unexpected_reward": response.nouls["unexpected_reward"].noul,
    }
    urgency_q = questions["urgency"]
    frustration_q = questions["frustration"]
    urgency_levels = len(urgency_q.criteria) - 1 if isinstance(urgency_q, Score) else 1
    frustration_levels = len(frustration_q.criteria) - 1 if isinstance(frustration_q, Score) else 1
    urgency_norm = response.scores["urgency"].score / max(1, urgency_levels)
    frustration_norm = response.scores["frustration"].score / max(1, frustration_levels)
    return compose_triage(
        route_choice=route_answer.choice,
        route_conf=route_answer.confidence,
        spam_parts=spam_parts,
        urgency=urgency_norm,
        frustration=frustration_norm,
        needs_memory=response.nouls["needs_memory"].noul,
        refund=response.nouls["refund_requested"].noul,
        config=config,
        pii_detected=response.nouls["pii_detected"].noul,
    )
