"""Plugin registries. Open/Closed: add files, don't edit core."""

from __future__ import annotations

from typing import Protocol

from .schemas import HandlerResult, Ticket, TriageResult


class Handler(Protocol):
    """A route handler. Implement + register, never branch core triage."""

    name: str

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True if this handler owns the triage route."""
        ...

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """Execute deterministic work for this route."""
        ...


HANDLERS: dict[str, Handler] = {}


def register(handler: Handler) -> Handler:
    """Register a handler by name. Safe to call at import time."""
    HANDLERS[handler.name] = handler
    return handler


class MemoryBackend(Protocol):
    """Pluggable memory store. SQLite now, Postgres/supermemory later.

    Version history: v0.2 added list/delete/count for the memory-platform
    surface. Implementations must provide all five methods.
    """

    def store(self, tenant_id: str, text: str, type: str) -> str:
        """Persist text, return id."""
        ...

    def search_bm25(self, tenant_id: str, query: str, top_k: int) -> list[dict[str, str]]:
        """Lexical shortlist; Jev reranks afterwards. Return [{id,text,type}]."""
        ...

    def list(self, tenant_id: str, limit: int) -> list[dict[str, str]]:
        """Newest-first rows for a tenant. Return [{id,text,type}]."""
        ...

    def delete(self, mem_id: str, tenant_id: str | None = None) -> bool:
        """Delete one row by id, optionally scoped to a tenant.

        A tenant mismatch reports False, exactly like a missing id, so
        ids cannot be used as cross-tenant deletion oracles.
        """
        ...

    def count(self, tenant_id: str) -> int:
        """Number of rows for a tenant."""
        ...
