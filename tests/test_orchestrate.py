"""Orchestrator tests: gating, draft honesty, additive API shape. Offline only."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from backend.main import app
from backend.orchestrator import (
    build_draft_reply,
    orchestrate_offline,
    orchestration_thresholds,
    seed_default_docs,
)
from backend.schemas import Customer, HandlerResult, Sender, Ticket, TriageAction, TriageResult
from backend.triage import compose_triage

TICKET = Ticket(
    subject="Duplicate charge",
    message="Charged twice for A-104, refund please.",
    sender=Sender(display_name="Acme", email="user@acme.com"),
)
CUSTOMER = Customer(plan="enterprise", open_orders=("A-104",))
HANDLER = HandlerResult(
    handler="billing",
    ticket_subject="Duplicate charge",
    summary="Refund duplicate.",
    next_step="Issue refund.",
)
CANDIDATES = [{"id": "d1", "text": "Refund policy: duplicates eligible.", "type": "doc"}]
SCORES = {"d1": {"relevance": 0.9, "contradicts": 0.0, "injection": 0.0, "pii": 0.0}}
CONFIG = {"orchestration": {"needs_memory_threshold": 0.6, "max_memory_hits": 5}}


def _triage(needs_memory: float = 0.8) -> TriageResult:
    return compose_triage(
        route_choice="billing",
        route_conf=0.9,
        spam_parts={
            "requests_credentials": 0.0,
            "sender_identity_mismatch": 0.0,
            "unexpected_reward": 0.0,
        },
        urgency=0.5,
        frustration=0.2,
        needs_memory=needs_memory,
        refund=0.9,
        config={},
    )


def test_thresholds_default_and_config() -> None:
    assert orchestration_thresholds({}) == (0.60, 5)
    assert orchestration_thresholds(CONFIG) == (0.60, 5)
    assert orchestration_thresholds(
        {"orchestration": {"needs_memory_threshold": 0.9, "max_memory_hits": 2}}
    ) == (
        0.9,
        2,
    )


def test_offline_recalls_when_needs_memory_high() -> None:
    res = orchestrate_offline(
        TICKET, _triage(0.8), HANDLER, CANDIDATES, SCORES, "supported", 0.1, CONFIG
    )
    assert len(res.memory_hits) == 1
    assert res.memory_hits[0].id == "d1"
    assert res.verify.verdict == "supported"
    assert "[d1]" in res.draft_reply  # draft cites its evidence.


def test_offline_skips_recall_when_needs_memory_low() -> None:
    res = orchestrate_offline(
        TICKET, _triage(0.1), HANDLER, CANDIDATES, SCORES, "supported", 0.1, CONFIG
    )
    assert res.memory_hits == ()
    assert "below threshold" in res.draft_reply


def test_draft_without_evidence_is_honest() -> None:
    triage = _triage(0.1)
    draft = build_draft_reply(TICKET, triage, HANDLER, [])
    assert "no hits passed the relevance gates" in draft
    assert "Refund duplicate." in draft
    skipped = build_draft_reply(TICKET, triage, HANDLER, [], recalled=False)
    assert "below threshold" in skipped


def test_seed_is_idempotent() -> None:
    from backend.memory_backends.sqlite import SqliteMemoryBackend

    backend = SqliteMemoryBackend(":memory:")
    assert seed_default_docs(backend, "t1") == 3
    assert seed_default_docs(backend, "t1") == 0
    backend.close()


def test_orchestrate_action_still_gated() -> None:
    triage = _triage(0.8)
    assert triage.action == TriageAction.AUTO_ROUTE


def test_orchestrate_needs_key() -> None:
    saved = os.environ.pop("TYPESAFE_API_KEY", None)
    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.post(
            "/v1/orchestrate",
            json={"ticket": {"subject": "s", "message": "m"}, "tenant_id": "t"},
        )
        assert res.status_code == 503
        assert "TYPESAFE_API_KEY" in res.json()["detail"]
    finally:
        if saved is not None:
            os.environ["TYPESAFE_API_KEY"] = saved


def test_existing_routes_unchanged() -> None:
    client = TestClient(app)
    assert client.get("/healthz").json() == {"status": "ok"}
    res = client.post("/v1/triage", json={"ticket": {"subject": "s", "message": "m"}})
    assert res.status_code == 200
    assert "route" in res.json()


def test_memory_crud_endpoints(monkeypatch) -> None:
    """Store/list/count/delete memories round-trip without Jev."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod
    from backend.memory_backends.sqlite import SqliteMemoryBackend

    backend = SqliteMemoryBackend(":memory:")
    monkeypatch.setattr(main_mod, "memory_backend", lambda: backend)
    try:
        client = TestClient(app)
        stored = client.post(
            "/v1/memory/store",
            json={"tenant_id": "t", "text": "Refund policy doc", "type": "doc"},
        ).json()
        assert client.get("/v1/memory/count", params={"tenant_id": "t"}).json() == {"count": 1}
        rows = client.get("/v1/memory/list", params={"tenant_id": "t"}).json()
        assert rows[0]["text"] == "Refund policy doc"
        assert client.delete(f"/v1/memory/{stored['id']}", params={"tenant_id": "t"}).json() == {
            "deleted": True
        }
        assert client.get("/v1/memory/count", params={"tenant_id": "t"}).json() == {"count": 0}
    finally:
        backend.close()


def test_orchestrate_auto_captures_resolved(monkeypatch) -> None:
    """Auto_route results are stored back as decision memories."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod
    from backend.memory_backends.sqlite import SqliteMemoryBackend
    from backend.orchestrator import orchestrate_offline

    backend = SqliteMemoryBackend(":memory:")
    monkeypatch.setattr(main_mod, "memory_backend", lambda: backend)
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")

    async def fake_live(ticket, customer, tenant_id, _backend, resolver, config_path="config.yaml"):
        triage = _triage(0.8)
        return orchestrate_offline(
            ticket, triage, resolver(ticket, triage), [], {}, "supported", 0.1, CONFIG
        )

    monkeypatch.setattr(main_mod, "orchestrate_live", fake_live)
    client = TestClient(app)
    res = client.post(
        "/v1/orchestrate",
        json={"ticket": {"subject": "s", "message": "m"}, "tenant_id": "cap"},
    )
    assert res.status_code == 200
    assert res.json()["captured_memory_id"] != ""
    rows = backend.list("cap", 100)
    assert [r for r in rows if r["type"] == "decision"] != []
    assert backend.count("cap") == 4  # 3 seeded policy docs + 1 captured decision.
    backend.close()


def test_top_level_extra_fields_rejected() -> None:
    """Frozen wrappers 422 on unknown top-level fields instead of ignoring them."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    res = client.post(
        "/v1/triage",
        json={"ticket": {"subject": "s", "message": "m"}, "zzz_unknown": 123},
    )
    assert res.status_code == 422


def test_null_sender_coerced_to_defaults() -> None:
    """Explicit null sender behaves like an omitted sender (lenient, 200)."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    res = client.post(
        "/v1/triage",
        json={
            "ticket": {
                "subject": "VPN",
                "message": "VPN not working please help",
                "sender": {"display_name": None, "email": None},
            }
        },
    )
    assert res.status_code == 200


def test_delete_is_tenant_scoped(monkeypatch) -> None:
    """Ids cannot delete another tenant's memories."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod
    from backend.memory_backends.sqlite import SqliteMemoryBackend

    backend = SqliteMemoryBackend(":memory:")
    monkeypatch.setattr(main_mod, "memory_backend", lambda: backend)
    try:
        client = TestClient(app)
        mem_id = client.post(
            "/v1/memory/store", json={"tenant_id": "a", "text": "secret", "type": "doc"}
        ).json()["id"]
        assert client.delete(f"/v1/memory/{mem_id}", params={"tenant_id": "b"}).json() == {
            "deleted": False
        }
        assert client.get("/v1/memory/count", params={"tenant_id": "a"}).json() == {"count": 1}
        assert client.delete(f"/v1/memory/{mem_id}", params={"tenant_id": "a"}).json() == {
            "deleted": True
        }
    finally:
        backend.close()


def test_store_validates_type_and_text() -> None:
    """Unknown types and empty text are 422, not silent coercion."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    assert (
        client.post(
            "/v1/memory/store", json={"tenant_id": "t", "text": "x", "type": "banana"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/memory/store", json={"tenant_id": "t", "text": "   ", "type": "doc"}
        ).status_code
        == 422
    )


def test_api_key_gate(monkeypatch) -> None:
    """Protected routes 401 without the key; healthz stays open."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod

    monkeypatch.setenv("PULSEDESK_API_KEY", "secret123")
    client = TestClient(main_mod.app)
    assert client.get("/healthz").status_code == 200
    no_key = client.post("/v1/triage", json={"ticket": {"subject": "s", "message": "m"}})
    assert no_key.status_code == 401
    wrong = client.post(
        "/v1/triage",
        json={"ticket": {"subject": "s", "message": "m"}},
        headers={"X-API-Key": "wrong"},
    )
    assert wrong.status_code == 401
    ok_case = client.post(
        "/v1/triage",
        json={"ticket": {"subject": "s", "message": "m"}},
        headers={"X-API-Key": "secret123"},
    )
    assert ok_case.status_code == 200


def test_auth_open_without_env(monkeypatch) -> None:
    """Dev mode: no PULSEDESK_API_KEY means no gate (documented)."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod

    monkeypatch.delenv("PULSEDESK_API_KEY", raising=False)
    client = TestClient(main_mod.app)
    res = client.post("/v1/triage", json={"ticket": {"subject": "s", "message": "m"}})
    assert res.status_code == 200


def test_delete_requires_tenant(monkeypatch) -> None:
    """Tenant scoping is mandatory on delete (no unscoped fallback)."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod
    from backend.memory_backends.sqlite import SqliteMemoryBackend

    backend = SqliteMemoryBackend(":memory:")
    monkeypatch.setattr(main_mod, "memory_backend", lambda: backend)
    try:
        client = TestClient(main_mod.app)
        mem_id = client.post(
            "/v1/memory/store", json={"tenant_id": "t", "text": "x", "type": "doc"}
        ).json()["id"]
        assert client.delete(f"/v1/memory/{mem_id}").status_code == 422
        assert client.delete(f"/v1/memory/{mem_id}", params={"tenant_id": ""}).status_code == 422
        assert backend.count("t") == 1
    finally:
        backend.close()


def test_rate_limit_429_with_retry_after(monkeypatch) -> None:
    """Excess requests get 429 + Retry-After instead of silent slowdown."""
    from fastapi.testclient import TestClient

    import backend.main as main_mod

    monkeypatch.setenv("PULSEDESK_RATE_LIMIT", "2")
    main_mod._rate_hits.clear()
    client = TestClient(main_mod.app)
    body = {"ticket": {"subject": "s", "message": "m"}}
    assert client.post("/v1/triage", json=body).status_code == 200
    assert client.post("/v1/triage", json=body).status_code == 200
    limited = client.post("/v1/triage", json=body)
    assert limited.status_code == 429
    assert limited.headers.get("retry-after") == "60"
    main_mod._rate_hits.clear()
