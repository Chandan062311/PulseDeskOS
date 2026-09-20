"""Shared frozen contracts. Single source of truth for all agents.

Rule: change shapes here + bump API version, never ad-hoc dicts in handlers.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _empty_if_none(value: object) -> object:
    """Coerce explicit JSON null to "" so omission and null agree."""
    return "" if value is None else value


NonNullStr = Annotated[str, BeforeValidator(_empty_if_none)]


class Frozen(BaseModel):
    """Base for all contracts: immutable, no extra fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Route(StrEnum):
    """Stable routing targets. Add new members, never rename existing."""

    IT_ACCESS = "it_access"
    BUG_REPORT = "bug_report"
    BILLING = "billing"
    HR_POLICY = "hr_policy"
    OTHER = "other"


class Sender(Frozen):
    """Ticket sender. Explicit nulls coerce to "" via :data:`NonNullStr`."""

    display_name: NonNullStr = ""
    email: NonNullStr = ""


class Link(Frozen):
    """Hyperlink attached to a ticket."""

    text: str = ""
    url: str = ""


class Ticket(Frozen):
    """Incoming support ticket with sender context and links."""

    subject: str = ""
    message: str
    sender: Sender = Field(default_factory=Sender)
    links: tuple[Link, ...] = ()


class Customer(Frozen):
    """Customer context: plan tier plus open order ids."""

    plan: str = "enterprise"
    open_orders: tuple[str, ...] = ()


class TriageAction(StrEnum):
    """Triage outcome: auto-route, human review, or spam quarantine."""

    AUTO_ROUTE = "auto_route"
    HUMAN_REVIEW = "human_review"
    QUARANTINE_SPAM = "quarantine_spam"


class TriageResult(Frozen):
    """Composed triage: route plus risk scores plus the gated action."""

    route: Route
    route_confidence: float = Field(ge=0.0, le=1.0)
    spam_risk: float = Field(ge=0.0, le=1.0)
    urgency: float
    frustration: float
    needs_memory: float = Field(ge=0.0, le=1.0)
    refund_requested: float = Field(ge=0.0, le=1.0)
    pii_detected: float = Field(ge=0.0, le=1.0, default=0.0)
    action: TriageAction
    reason: str = ""


class MemoryHit(Frozen):
    """Reranked memory hit with relevance plus safety-gate scores."""

    id: str
    text: str
    type: Literal["ticket", "doc", "decision"] = "doc"
    relevance: float = Field(ge=0.0, le=1.0)
    contradicts: float = Field(ge=0.0, le=1.0, default=0.0)
    has_injection: float = Field(ge=0.0, le=1.0, default=0.0)
    has_pii: float = Field(ge=0.0, le=1.0, default=0.0)


class VerifyResult(Frozen):
    """Verification verdict for a draft reply against evidence."""

    supported: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    verdict: Literal["supported", "needs_review", "unsupported"]


class HandlerResult(Frozen):
    """Deterministic output from the handler that owned a ticket."""

    handler: str
    ticket_subject: str = ""
    summary: str = ""
    next_step: str = ""


class OrchestrateResponse(Frozen):
    """Full pipeline result. Additive contract: existing routes unchanged."""

    triage: TriageResult
    memory_hits: tuple[MemoryHit, ...] = ()
    handler: HandlerResult
    draft_reply: str = ""
    verify: VerifyResult
    captured_memory_id: str = ""  # v0.3: auto-captured decision id, "" when skipped.
