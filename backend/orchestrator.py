"""Full orchestration: triage -> conditional recall -> dispatch -> verify.

Code owns the workflow; Jev supplies one judgment battery per stage.
Additive layer only: ``triage``, ``memory``, ``verify``, and ``registry``
modules are untouched. New routes must call in here, never reimplement
the chain.

Pipeline (thresholds from ``config.yaml`` → ``orchestration``):
1. ``triage_live`` — 8 parallel judgments, composed with gates.
2. If ``triage.needs_memory >= needs_memory_threshold`` — ``recall_live``
   (BM25 shortlist + Jev rerank). Otherwise ``memory_hits`` is empty.
3. Caller-supplied ``handler_resolver`` (``main.dispatch``) — registry
   dispatch, no route-string branching.
4. Deterministic ``build_draft_reply`` from handler + memory evidence.
5. ``verify_live`` of the draft against the evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .jev_client import load_config
from .memory import compose_recall, recall_live
from .registry import MemoryBackend
from .schemas import (
    Customer,
    HandlerResult,
    MemoryHit,
    OrchestrateResponse,
    Ticket,
    TriageResult,
    VerifyResult,
)
from .verify import compose_verify, verify_live

SEED_DOCS: tuple[tuple[str, str], ...] = (
    ("doc", "Refund policy: duplicate charges are eligible for a full refund."),
    ("doc", "VPN access: new joiners are provisioned on their start date via IT."),
    ("doc", "Outage runbook: API 500s are SEV-1, page on-call, post status update."),
)

_DEFAULT_NEEDS_MEMORY = 0.60
_DEFAULT_MAX_HITS = 5


def orchestration_thresholds(config: dict[str, Any] | None) -> tuple[float, int]:
    """Return (needs_memory_threshold, max_memory_hits) from config.

    Args:
        config: Parsed ``config.yaml`` mapping (may be empty).

    Returns:
        Threshold for triggering recall plus the cap on returned hits.
    """
    orch = (config or {}).get("orchestration", {})
    if not isinstance(orch, dict):
        orch = {}
    threshold = orch.get("needs_memory_threshold", _DEFAULT_NEEDS_MEMORY)
    max_hits = orch.get("max_memory_hits", _DEFAULT_MAX_HITS)
    try:
        threshold_f = float(threshold)
    except (TypeError, ValueError):
        threshold_f = _DEFAULT_NEEDS_MEMORY
    try:
        max_hits_i = int(max_hits)
    except (TypeError, ValueError):
        max_hits_i = _DEFAULT_MAX_HITS
    return max(0.0, min(1.0, threshold_f)), max(0, max_hits_i)


def build_draft_reply(
    ticket: Ticket,
    triage: TriageResult,
    handler: HandlerResult,
    memory_hits: list[MemoryHit],
    recalled: bool = True,
) -> str:
    """Build a deterministic draft reply from handler output + evidence.

    No LLM here by design: the draft is a template so every claim traces
    to either the handler summary or a cited memory hit, which is exactly
    what the verify stage checks.

    Args:
        ticket: Incoming support ticket.
        triage: Composed triage result.
        handler: Dispatched handler output.
        memory_hits: Reranked evidence (may be empty).
        recalled: Whether the recall stage ran. Distinguishes "recall ran
            but nothing passed the gates" from "recall never ran".

    Returns:
        Plain-text draft reply with evidence citations.
    """
    lines = [
        f"Subject: Re: {ticket.subject or '(no subject)'}",
        "",
        handler.summary,
        f"Next step: {handler.next_step}",
    ]
    if memory_hits:
        lines.append("")
        lines.append("Evidence:")
        for hit in memory_hits:
            lines.append(f"- [{hit.id[:8]}] {hit.text}")
    elif recalled:
        lines.append("")
        lines.append("Evidence: recall ran but no hits passed the relevance gates.")
    else:
        lines.append("")
        lines.append("Evidence: none retrieved (needs_memory below threshold).")
    lines.append("")
    lines.append(f"Route: {triage.route.value} (confidence {triage.route_confidence:.2f}).")
    return "\n".join(lines)


def orchestrate_offline(
    ticket: Ticket,
    triage: TriageResult,
    handler: HandlerResult,
    candidates: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    verify_choice: str,
    verify_needs_review: float,
    config: dict[str, Any] | None = None,
) -> OrchestrateResponse:
    """Compose a full pipeline result from mock answers. Pure offline helper.

    Applies the same recall gating as the live path: candidates are only
    composed when ``triage.needs_memory`` meets the configured threshold.

    Args:
        ticket: Incoming support ticket.
        triage: Pre-composed triage result (e.g. via ``compose_triage``).
        handler: Pre-dispatched handler result.
        candidates: BM25-style shortlist for the recall stage.
        scores: Mock Jev scores keyed by candidate id.
        verify_choice: Mock support choice (supported/contradicted/unsupported).
        verify_needs_review: Mock needs_review Noul.
        config: Parsed ``config.yaml`` mapping for thresholds.

    Returns:
        Complete :class:`OrchestrateResponse`.
    """
    cfg = config or {}
    threshold, max_hits = orchestration_thresholds(cfg)
    recalled = triage.needs_memory >= threshold
    hits = compose_recall(candidates, scores, cfg) if recalled else []
    hits = hits[:max_hits]
    draft = build_draft_reply(ticket, triage, handler, hits, recalled)
    verify = compose_verify(verify_choice, verify_needs_review)
    return OrchestrateResponse(
        triage=triage,
        memory_hits=tuple(hits),
        handler=handler,
        draft_reply=draft,
        verify=verify,
    )


async def orchestrate_live(
    ticket: Ticket,
    customer: Customer,
    tenant_id: str,
    backend: MemoryBackend,
    handler_resolver: Callable[[Ticket, TriageResult], HandlerResult],
    config_path: str = "config.yaml",
) -> OrchestrateResponse:
    """Run the full live pipeline. Needs ``TYPESAFE_API_KEY``.

    Args:
        ticket: Incoming support ticket.
        customer: Customer context for triage.
        tenant_id: Memory tenant for recall.
        backend: ``MemoryBackend`` for the recall shortlist.
        handler_resolver: Registry dispatch callable (``main.dispatch``).
        config_path: Path to ``config.yaml``.

    Returns:
        Complete :class:`OrchestrateResponse` from live Jev answers.

    Raises:
        RuntimeError: If ``TYPESAFE_API_KEY`` is not set.
    """
    from .triage import triage_live  # local import: keeps module import light.

    config = load_config(config_path)
    triage = await triage_live(ticket, customer, config_path)
    threshold, max_hits = orchestration_thresholds(config)
    hits: list[MemoryHit] = []
    recalled = triage.needs_memory >= threshold
    if recalled:
        hits = (await recall_live(tenant_id, ticket.message, backend, config_path))[:max_hits]
    handler = handler_resolver(ticket, triage)
    draft = build_draft_reply(ticket, triage, handler, hits, recalled)
    evidence = "\n".join(hit.text for hit in hits) or "No retrieved evidence."
    verify: VerifyResult = await verify_live(draft, evidence, config_path)
    return OrchestrateResponse(
        triage=triage,
        memory_hits=tuple(hits),
        handler=handler,
        draft_reply=draft,
        verify=verify,
    )


def seed_default_docs(backend: MemoryBackend, tenant_id: str) -> int:
    """Seed policy docs if the tenant store is empty. Idempotent.

    Args:
        backend: ``MemoryBackend`` to seed.
        tenant_id: Tenant to check and seed.

    Returns:
        Number of docs inserted (0 when the store already has rows).
    """
    existing = backend.search_bm25(tenant_id, "", 10000)
    if existing:
        return 0
    count = 0
    for mem_type, text in SEED_DOCS:
        backend.store(tenant_id, text, mem_type)
        count += 1
    return count
