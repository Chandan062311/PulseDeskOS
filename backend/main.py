"""FastAPI surface (Agent A).

Endpoints:
- ``GET /healthz``: liveness probe.
- ``POST /v1/triage``: Ticket + Customer -> TriageResult. Offline midpoint mock
  by default; live Jev when ``?live=true`` and ``TYPESAFE_API_KEY`` is set.
- ``POST /v1/ingest``: Same triage plus handler dispatch via the
  ``HANDLERS`` registry (never if-else on route strings).
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import Field

from .handlers import builtins as _builtins  # noqa: F401  (side-effect registration)
from .jev_client import load_config, require_api_key
from .memory import recall_live
from .memory_backends.sqlite import SqliteMemoryBackend
from .orchestrator import orchestrate_live, seed_default_docs
from .registry import HANDLERS
from .schemas import (
    Customer,
    Frozen,
    HandlerResult,
    MemoryHit,
    OrchestrateResponse,
    Ticket,
    TriageAction,
    TriageResult,
    VerifyResult,
)
from .triage import MID_MOCK_ANSWERS, triage_live, triage_offline
from .verify import verify_live

logger = logging.getLogger("pulsedesk")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def log_jev_status() -> None:
    """Log once whether live Jev is configured (call at startup)."""
    from .jev_client import require_api_key

    try:
        key = require_api_key()
        logger.info("jev live (key %s…%s)", key[:7], key[-4:])
    except RuntimeError:
        logger.warning("jev OFFLINE: TYPESAFE_API_KEY unset — live routes will 503")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup hook: report Jev key posture exactly once (never blocks)."""
    log_jev_status()
    yield


app = FastAPI(title="PulseDesk OS", lifespan=lifespan)

# Browser calls from the console (:5173 dev, :8080 prod) are cross-origin.
# Origins are configurable; same-origin deployments need none of this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "PULSEDESK_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Browser calls from the console (:5173 dev, :8080 prod) are cross-origin.
# Origins are configurable; same-origin deployments need none of this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "PULSEDESK_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class TriageRequest(Frozen):
    """Triage request body: ticket plus optional customer context."""

    ticket: Ticket
    customer: Customer = Field(default_factory=Customer)


class IngestResponse(Frozen):
    """Ingest response: triage result plus the dispatched handler output."""

    triage: TriageResult
    handler: HandlerResult


class MemoryStoreRequest(Frozen):
    """Memory store request body."""

    tenant_id: str = "default"
    text: str
    type: Literal["ticket", "doc", "decision"] = "doc"


class MemoryRecallRequest(Frozen):
    """Memory recall request body."""

    tenant_id: str = "default"
    query: str
    top_k: int = 5


class VerifyRequest(Frozen):
    """Verify request body: draft reply plus evidence text."""

    reply: str
    evidence: str


class OrchestrateRequest(Frozen):
    """Full pipeline request body."""

    ticket: Ticket
    customer: Customer = Field(default_factory=Customer)
    tenant_id: str = "default"
    seed: bool = True


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach a request id and log latency. Observability, no behavior change."""
    request_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("%s %s %s %.1fms", request_id, request.method, request.url.path, elapsed_ms)
    response.headers["X-Request-Id"] = request_id
    return response


_RATE_WINDOW_S = 60.0
_rate_hits: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def _rate_limit_per_minute() -> int:
    """Reads ``PULSEDESK_RATE_LIMIT`` per call so tests can retune it."""
    try:
        return max(int(os.environ.get("PULSEDESK_RATE_LIMIT", "120")), 1)
    except ValueError:
        return 120


@app.middleware("http")
async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Sliding-window rate limit per client IP. 429 with Retry-After on excess."""
    if request.url.path == "/healthz":
        return await call_next(request)
    limit = _rate_limit_per_minute()
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_lock:
        hits = [t for t in _rate_hits.get(client, []) if now - t < _RATE_WINDOW_S]
        if len(hits) >= limit:
            return JSONResponse(  # type: ignore[return-value]
                status_code=429,
                content={"detail": "Rate limit exceeded. Slow down and retry."},
                headers={"Retry-After": "60"},
            )
        hits.append(now)
        _rate_hits[client] = hits
    return await call_next(request)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Map config errors (e.g. missing API key) to 503, not 500."""
    logger.warning("503 %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@lru_cache(maxsize=1)
def memory_backend() -> SqliteMemoryBackend:
    """Shared SQLite backend singleton. Path from MEMORY_DB, default memory.db."""
    return SqliteMemoryBackend(os.environ.get("MEMORY_DB", "memory.db"))


def _auto_capture_enabled() -> bool:
    """Whether resolved tickets are captured back as decision memories."""
    try:
        mem = load_config().get("memory", {})
        return bool(mem.get("auto_capture_resolved", True)) if isinstance(mem, dict) else True
    except OSError:
        return True


def dispatch(ticket: Ticket, triage: TriageResult) -> HandlerResult:
    """Dispatch to the first registered handler that claims the triage.

    Args:
        ticket: Incoming support ticket.
        triage: Composed triage result.

    Returns:
        The owning handler's result, or an ``unrouted`` fallback when no
        registered handler claims the triage.
    """
    for handler in HANDLERS.values():
        if handler.can_handle(triage):
            return handler.run(ticket, triage)
    return HandlerResult(
        handler="unrouted",
        ticket_subject=ticket.subject,
        summary="No registered handler claimed this triage.",
        next_step="Send to the human review queue.",
    )


async def _triage_request(body: TriageRequest, live: bool) -> TriageResult:
    """Run offline mock triage, or live Jev when requested and keyed.

    Args:
        body: Ticket + customer payload.
        live: When True and ``TYPESAFE_API_KEY`` is set, call live Jev.

    Returns:
        Composed :class:`TriageResult`.
    """
    if live and os.environ.get("TYPESAFE_API_KEY"):
        return await triage_live(body.ticket, body.customer)
    return triage_offline(body.ticket, body.customer, dict(MID_MOCK_ANSWERS))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe.

    Returns:
        ``{"status": "ok"}`` when the service is up.
    """
    return {"status": "ok"}


@app.get("/v1/status")
def v1_status() -> dict[str, str]:
    """Setup status: is live Jev configured? Never exposes the key itself."""
    try:
        require_api_key()
        return {"status": "ok", "jev": "live"}
    except RuntimeError:
        return {"status": "ok", "jev": "offline"}


@app.post("/v1/triage")
async def v1_triage(body: TriageRequest, live: bool = False) -> TriageResult:
    """Triage a ticket.

    Args:
        body: Ticket + customer payload.
        live: Use live Jev when True and an API key is configured.

    Returns:
        Composed :class:`TriageResult`.
    """
    return await _triage_request(body, live)


@app.post("/v1/ingest")
async def v1_ingest(body: TriageRequest, live: bool = False) -> IngestResponse:
    """Triage a ticket and run the owning registered handler.

    Args:
        body: Ticket + customer payload.
        live: Use live Jev when True and an API key is configured.

    Returns:
        Triage result plus handler output.
    """
    triage = await _triage_request(body, live)
    return IngestResponse(triage=triage, handler=dispatch(body.ticket, triage))


@app.post("/v1/memory/store")
def v1_memory_store(body: MemoryStoreRequest) -> dict[str, str]:
    """Store a memory doc for a tenant. Returns the new id."""
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="text must be non-empty.")
    mem_id = memory_backend().store(body.tenant_id, body.text, body.type)
    return {"id": mem_id}


@app.post("/v1/memory/seed")
def v1_memory_seed(tenant_id: str = "default") -> dict[str, int]:
    """Seed default policy docs when the tenant store is empty. Idempotent."""
    return {"seeded": seed_default_docs(memory_backend(), tenant_id)}


@app.post("/v1/memory/recall")
async def v1_memory_recall(body: MemoryRecallRequest, live: bool = True) -> list[MemoryHit]:
    """Recall reranked memory hits. Live Jev only (no offline mode)."""
    if not live:
        raise RuntimeError("Memory recall is live-only: retry without live=false.")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("Memory recall needs live Jev: set TYPESAFE_API_KEY.")
    hits = await recall_live(body.tenant_id, body.query, memory_backend())
    return hits[: max(body.top_k, 0)]


@app.get("/v1/memory/list")
def v1_memory_list(tenant_id: str = "default", limit: int = 20) -> list[dict[str, str]]:
    """List newest-first memories for a tenant (no Jev call)."""
    return memory_backend().list(tenant_id, limit)


@app.delete("/v1/memory/{mem_id}")
def v1_memory_delete(mem_id: str, tenant_id: str) -> dict[str, bool]:
    """Delete one memory by id within a tenant (required).

    Tenant scoping is mandatory: without it, bare ids were a cross-tenant
    deletion oracle. Mismatches report ``deleted: false`` like a missing id.
    """
    if not tenant_id.strip():
        raise HTTPException(status_code=422, detail="tenant_id must be non-empty.")
    return {"deleted": memory_backend().delete(mem_id, tenant_id)}


@app.get("/v1/memory/count")
def v1_memory_count(tenant_id: str = "default") -> dict[str, int]:
    """Count memories for a tenant."""
    return {"count": memory_backend().count(tenant_id)}


@app.post("/v1/verify")
async def v1_verify(body: VerifyRequest) -> VerifyResult:
    """Verify a draft reply against evidence. Live Jev; 503 without a key."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("Verify needs live Jev: set TYPESAFE_API_KEY.")
    return await verify_live(body.reply, body.evidence)


@app.post("/v1/orchestrate")
async def v1_orchestrate(body: OrchestrateRequest) -> OrchestrateResponse:
    """Run the full pipeline: triage -> recall -> dispatch -> verify.

    Seeds default docs on first use when ``seed`` is true. Resolved
    auto_route tickets are captured back as decision memories when
    ``memory.auto_capture_resolved`` is true. Live Jev only; 503
    without an API key.
    """
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("Orchestration needs live Jev: set TYPESAFE_API_KEY.")
    if body.seed:
        seed_default_docs(memory_backend(), body.tenant_id)
    result = await orchestrate_live(
        body.ticket, body.customer, body.tenant_id, memory_backend(), dispatch
    )
    captured = ""
    if result.triage.action is TriageAction.AUTO_ROUTE and _auto_capture_enabled():
        captured = memory_backend().store(
            body.tenant_id,
            f"Resolved {result.triage.route.value}: {result.handler.summary} "
            f"Next: {result.handler.next_step}",
            "decision",
        )
    return result.model_copy(update={"captured_memory_id": captured})
