"""PulseDesk MCP server: triage, recall, and verify tools via FastMCP.

Tools run offline with mid-value stub scores so they work without an
API key; every response notes that live Jev calls require
``TYPESAFE_API_KEY``. The triage module is owned by another agent, so its
import is guarded and the server falls back to inline compose.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

if __package__:
    # Imported as backend.mcp_server (tests, app, python -m).
    from .handlers import builtins as _builtins
    from .jev_client import load_config
    from .memory import compose_recall
    from .memory_backends.sqlite import SqliteMemoryBackend
    from .orchestrator import SEED_DOCS
    from .schemas import Customer, MemoryHit, Sender, Ticket, VerifyResult
    from .triage import MID_MOCK_ANSWERS, triage_offline
    from .verify import compose_verify
else:
    # Run as a script: fastmcp run backend/mcp_server.py (no parent package).
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.handlers import (
        builtins as _builtins,  # noqa: F401  (side-effect registration)
    )
    from backend.jev_client import load_config
    from backend.memory import compose_recall
    from backend.memory_backends.sqlite import SqliteMemoryBackend
    from backend.orchestrator import SEED_DOCS
    from backend.schemas import Customer, MemoryHit, Sender, Ticket, VerifyResult
    from backend.triage import MID_MOCK_ANSWERS, triage_offline
    from backend.verify import compose_verify

_MID_ANSWERS: dict[str, Any] = dict(MID_MOCK_ANSWERS)
_triage_offline = triage_offline

mcp = FastMCP("pulsedesk")

_OFFLINE_NOTE = "Offline stub with mid values; live Jev call requires TYPESAFE_API_KEY."

_MEMORY_TYPES = ("ticket", "doc", "decision")

_APPLIED_SEEDS: set[str] = set()


def _shared_backend() -> SqliteMemoryBackend:
    """Persistent store shared with the API (MEMORY_DB, default memory.db)."""

    return SqliteMemoryBackend(os.environ.get("MEMORY_DB", "memory.db"))


def _ensure_seed_docs(backend: SqliteMemoryBackend, tenant_id: str) -> None:
    """Seed policy docs once per tenant when its store is empty.

    Uses the same ``SEED_DOCS`` as the API so MCP-seeded and API-seeded
    tenants start from identical default docs.
    """
    if tenant_id in _APPLIED_SEEDS:
        return
    if backend.count(tenant_id) == 0:
        for doc_type, text in SEED_DOCS:
            backend.store(tenant_id, text, doc_type)
    _APPLIED_SEEDS.add(tenant_id)


def _recall_top_k() -> int:
    """Shortlist depth from config (``memory.bm25_top_k``)."""
    try:
        mem = load_config().get("memory", {})
        top_k = mem.get("bm25_top_k", 30) if isinstance(mem, dict) else 30
        return max(int(top_k), 1)
    except (OSError, TypeError, ValueError):
        return 30


def _req_str(tool: str, name: str, value: object) -> str:
    """Require a string tool argument; MCP has no 422 envelope."""
    if not isinstance(value, str):
        raise ValueError(f"{tool}: {name} must be a string, got {type(value).__name__}.")
    return value


def triage_ticket(subject: str, message: str, sender_email: str = "") -> dict[str, Any]:
    """Classify a ticket offline (mid values) or via triage when available."""
    subject = _req_str("triage_ticket", "subject", subject)
    message = _req_str("triage_ticket", "message", message)
    sender_email = _req_str("triage_ticket", "sender_email", sender_email)
    if _triage_offline is not None and _MID_ANSWERS is not None:
        ticket = Ticket(
            subject=subject,
            message=message,
            sender=Sender(email=sender_email),
        )
        result = _triage_offline(ticket, Customer(), dict(_MID_ANSWERS))
        return {**result.model_dump(), "note": _OFFLINE_NOTE}
    return {
        "route": "other",
        "route_confidence": 0.5,
        "spam_risk": 0.5,
        "urgency": 0.5,
        "frustration": 0.5,
        "needs_memory": 0.5,
        "refund_requested": 0.5,
        "pii_detected": 0.5,
        "action": "human_review",
        "reason": "triage module not built yet",
        "note": _OFFLINE_NOTE,
    }


def recall_memory(tenant_id: str, query: str) -> dict[str, Any]:
    """Recall over the persistent shared store (seeded with policy docs if empty)."""
    tenant_id = _req_str("recall_memory", "tenant_id", tenant_id)
    query = _req_str("recall_memory", "query", query)
    backend = _shared_backend()
    try:
        _ensure_seed_docs(backend, tenant_id)
        candidates = backend.search_bm25(tenant_id, query, top_k=_recall_top_k())
        query_tokens = set(query.lower().split())
        scores: dict[str, dict[str, float]] = {}
        for candidate in candidates:
            overlap = len(query_tokens & set(candidate["text"].lower().split()))
            relevance = overlap / max(len(query_tokens), 1)
            scores[candidate["id"]] = {
                "relevance": relevance,
                "contradicts": 0.1,
                "injection": 0.1,
                "pii": 0.0,
            }
        hits: list[MemoryHit] = compose_recall(candidates, scores)
        return {
            "hits": [hit.model_dump() for hit in hits],
            "candidates_considered": len(candidates),
            "note": _OFFLINE_NOTE,
        }
    finally:
        backend.close()


def add_memory(tenant_id: str, text: str, type: str = "doc") -> dict[str, Any]:
    """Store a memory for a tenant in the persistent shared store."""
    tenant_id = _req_str("add_memory", "tenant_id", tenant_id)
    text = _req_str("add_memory", "text", text)
    mem_type = _req_str("add_memory", "type", type)
    if not text.strip():
        raise ValueError("add_memory: text must be non-empty.")
    if mem_type not in _MEMORY_TYPES:
        raise ValueError(f"add_memory: type must be one of {_MEMORY_TYPES}.")
    backend = _shared_backend()
    try:
        mem_id = backend.store(tenant_id, text, mem_type)
        return {"id": mem_id, "tenant_id": tenant_id}
    finally:
        backend.close()


def list_memories(tenant_id: str, limit: int = 20) -> dict[str, Any]:
    """List newest-first memories for a tenant."""
    tenant_id = _req_str("list_memories", "tenant_id", tenant_id)
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("list_memories: limit must be a positive integer.")
    backend = _shared_backend()
    try:
        _ensure_seed_docs(backend, tenant_id)
        return {"memories": backend.list(tenant_id, limit), "count": backend.count(tenant_id)}
    finally:
        backend.close()


def verify_response(reply: str, evidence: str) -> dict[str, Any]:
    """Verify a reply offline with mid values (routes to needs_review)."""
    reply = _req_str("verify_response", "reply", reply)
    evidence = _req_str("verify_response", "evidence", evidence)
    _ = (reply, evidence)  # scored live; stub below uses mid values only.
    result: VerifyResult = compose_verify(
        "supported",
        0.5,
        {"supported": 0.5, "contradicted": 0.25, "unsupported": 0.25},
    )
    return {**result.model_dump(), "note": _OFFLINE_NOTE}


mcp.tool(triage_ticket)
mcp.tool(recall_memory)
mcp.tool(add_memory)
mcp.tool(list_memories)
mcp.tool(verify_response)


if __name__ == "__main__":
    mcp.run()
