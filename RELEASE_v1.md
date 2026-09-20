# PulseDesk OS v1.0 — Release Notes (2026-09-20)

Enterprise productivity orchestrator powered by TypeSafe Jev (System One).
Principle: code owns the workflow, Jev owns the judgments.

## What shipped

### 1. Full ticket pipeline (`backend/main.py`, `backend/orchestrator.py`)

| Method | Path | Description |
|---|---|---|
| GET | `/healthz` | Liveness check → `{"status":"ok"}` |
| POST | `/v1/triage` | Req1: Jev 9-question triage + gated action (offline mock by default; live with `?live=true`) |
| POST | `/v1/ingest` | Triage + registry dispatch via `HANDLERS` |
| POST | `/v1/orchestrate` | Full chain: triage → recall → dispatch → draft → verify (live Jev only) |
| POST | `/v1/verify` | Support verdict for a draft reply (live Jev only) |

- Req1 asks 9 questions per ticket (`backend/triage.py`
  `build_triage_questions`): `route` (Choice; its confidence is the route
  confidence, not a separate question), `needs_memory`, `requests_credentials`,
  `sender_identity_mismatch`, `unexpected_reward` (these three compose
  `spam_risk`), `refund_requested`, `pii_detected`, `urgency`, `frustration`.
  The composed `TriageResult` carries a `reason` string (field name is
  `reason`, not `rationale`).
- `TriageResult.action` is one of `auto_route`, `human_review`,
  `quarantine_spam`, derived from `config.yaml` thresholds (code in
  `backend/triage.py` holds fallback defaults only).
- Handlers: all five routes (`it_access`, `bug_report`, `billing`,
  `hr_policy`, `other`) are classes in the single module
  `backend/handlers/builtins.py`, registered via `register()` into the
  `HANDLERS` registry (`backend/handlers/__init__.py`, `backend/registry.py`);
  deterministic work only, no live Jev calls (only `load_config()` for
  `handlers.*` thresholds).
- Live-only routes (`orchestrate`, `memory/recall`, `verify`) return
  **503 with a clear message** when `TYPESAFE_API_KEY` is missing
  (`backend/main.py` `RuntimeError` → 503 handler). `POST /v1/triage`
  (and `/v1/ingest`) do **not** 503 without a key: with `?live=true` and no
  key they fall back to the offline midpoint mock (`_triage_request`).
  Every response carries `X-Request-Id` via the logging middleware and
  structured latency logs.

### 2. Memory platform (`backend/memory_backends/`, `POST /v1/memory/*`)

| Method | Path | Description |
|---|---|---|
| POST | `/v1/memory/store` | Store a tenant memory doc → `{id}` (422 on empty text; `type` is `Literal["ticket","doc","decision"]`) |
| POST | `/v1/memory/seed` | Idempotent default policy docs (`?tenant_id=`) |
| POST | `/v1/memory/recall` | BM25 shortlist + Jev rerank, live-only |
| GET | `/v1/memory/list` | Newest-first tenant memories (`?tenant_id=&limit=`) |
| GET | `/v1/memory/count` | Tenant memory size (`?tenant_id=`) |
| DELETE | `/v1/memory/{mem_id}` | Delete by id, tenant-scoped when `?tenant_id=` given (cross-tenant → `deleted: false`) |

- Req2: BM25 shortlist (`memory.bm25_top_k: 30`) from a pluggable store
  (SQLite now), Jev reranks per candidate for relevance plus
  contradicts / injection / PII gates (`backend/memory.py`
  `build_memory_questions`).
- `memory.auto_capture_resolved: true` — resolved `auto_route` tickets are
  stored back as `decision` memories (`config.yaml`, `backend/main.py`).
- Tenant-scoped deletes enforced in SQL (`backend/memory_backends/sqlite.py`
  `delete`); MCP `limit < 1` raises `ValueError`; MCP non-string inputs
  guarded (`_req_str` → `ValueError` on all 5 tools).

### 3. Claude Code plugin + MCP (Superpowers-style)

Per `README.md` — the repo **is** the plugin:

- `.claude-plugin/plugin.json` — name `pulsedesk`, `v0.3.0`
- `skills/triage/SKILL.md` — `/pulsedesk:triage`
- `skills/orchestrate/SKILL.md` — `/pulsedesk:orchestrate`
- `skills/memory/SKILL.md` — `/pulsedesk:memory`
- `agents/reviewer.md` — review-queue worker agent
- `.mcp.json` — bundled MCP server (5 tools: `triage_ticket`,
  `recall_memory`, `add_memory`, `list_memories`, `verify_response`),
  reusing the same `Ticket` / `MemoryHit` / `VerifyResult` schemas and
  returning `triage_offline` `TriageResult` dicts — no duplicate pydantic
  types. (`backend/mcp_server.py` imports `Ticket`, `MemoryHit`,
  `VerifyResult` directly; `TriageResult` flows through `triage_offline`.)
- `claude plugin validate` ✔ per `sandbox/brutal/REPORT.md`
  post-repair verification.

### 4. UI — Vite+React ops console (`frontend/`)

Per `README.md` / `frontend/README.md`: working Vite+React ops console with
sidebar nav (Triage / Pipeline / Review / System); `npm run dev` documented,
`npm run build` verified (`frontend/README.md`: "verified: vite build
succeeds -> dist/"). Production Stitch screens are **not yet generated**:
`frontend/stitch-prompts.md` holds 3 copy-paste prompts (Inbox dashboard,
Triage detail, Review queue) and `frontend/README.md` notes Stitch was
blocked on OAuth from that session — run in a connected client.

### 5. Evals + config

- `evals/golden-tickets.json`: 14 labeled tickets (all 5 routes, 3 actions —
  verified by count: billing 4, other 4, it_access 2, bug_report 2,
  hr_policy 2; auto_route 10, quarantine_spam 2, human_review 2).
- `evals/README.md`: ticket → confidence-plot → threshold-tuning workflow
  (thresholds moved in `config.yaml` only).
- Behavior thresholds live in `config.yaml` and are read via `load_config()`;
  modules keep fallback defaults only.

## Gates status (from `config.yaml` + `ARCHITECTURE.md`)

| Gate | Rule |
|---|---|
| `quarantine_spam` | `spam.spam_risk >= 0.60`; spam score = weighted sum (`requests_credentials` 0.45, `sender_identity_mismatch` 0.30, `unexpected_reward` 0.25) |
| `human_review` | `routing.topic_confidence_threshold`: `route_confidence < 0.75`, **or** spam risk strictly between `spam.uncertain_low` 0.40 and `spam.uncertain_high` 0.60 (edges exclusive: 0.40 → confidence gate, 0.60 → quarantine), **or** route `other` (`routing.other_always_review: true` — no owning team) |
| `auto_route` | Everything above the gates → `HANDLERS[route]` |
| Memory recall | Runs if `needs_memory >= 0.60` (`orchestration.needs_memory_threshold`, not `memory:`); keeps `memory.keep_relevance_threshold >= 0.70`, drops `injection >= memory.drop_injection_threshold 0.30`, flags `contradicts >= memory.contradict_flag_threshold 0.60`; `orchestration.max_memory_hits: 5` |
| Verify | `needs_review_threshold: 0.5` (`verify.needs_review_threshold`) |

Verification status (per `sandbox/report.md`, `sandbox/brutal/REPORT.md`):

- Sandbox Monday-morning queue: **5/5 match expectations**
  (outage → `bug_report/auto_route`; billing → `billing/auto_route`;
  VPN → `it_access/auto_route`; phish → `other/quarantine_spam`;
  vague → `other/human_review`).
- Brutal sweep: 4 adversarial agents, 60+ cases, **0 crashes**
  (no 500 on any bad input).
- Post-repair per `sandbox/brutal/REPORT.md` + `REPORT_V2.md`: 55 pytest passed, `ruff` +
  format + `mypy` (strict) clean, `claude plugin validate` ✔, live goldens
  14/14 joint (incl. 2 new hr_policy), sandbox problem statement 5/5 with
  exit 0, UI 200, API ok. No other pass counts are claimed here.
- Two sandbox bugs fixed + regression-tested: SQLite threading crash
  (`check_same_thread=False` + lock) and confident-`other` backstop
  (`other_always_review`).

## Known limitations (backlog — `sandbox/brutal/REPORT.md`, mapped, not yet built)

1. **Pre-Jev PII redaction** — the `pii_detected` signal exists (9th
   question; live SSN+card scored 0.99), but raw text still reaches Jev.
2. **50KB+ doc chunking** — BM25 retrieves large docs, but Jev relevance
   dilutes below the 0.70 keep threshold.
3. **Dropped-candidate reason codes** — recall responses do not yet explain
   why candidates were filtered.
4. **Backend audit log as review-queue source of truth** — the UI
   currently uses session state.

Fixed before release (not limitations): split `recall?live=false` 503
messages (live-only vs missing-key).

Accepted as designed (documented, not changed): single-label collapse of
dual-intent tickets; duplicates allowed (no dedup); unknown query params
ignored (FastAPI default); missing Content-Type 422 wording (framework
default); 20-way offline latency ~200ms vs 1–2ms sequential (threadpool
overhead, zero errors).

## Try it

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set TYPESAFE_API_KEY (https://console.typesafe.ai/keys)
uvicorn backend.main:app --reload
pytest

# Production run
docker build -t pulsedesk-os .
docker run -p 8000:8000 --env-file .env -v pddata:/data pulsedesk-os

# Plugin (Claude Code)
claude --plugin-dir ./pulsedesk-os          # try: /pulsedesk:triage …
claude plugin validate ./pulsedesk-os       # ✔ Validation passed

# MCP without the plugin
/tmp/opencode/pdvenv/bin/fastmcp run backend/mcp_server.py   # from pulsedesk-os/
claude mcp add pulsedesk -- /tmp/opencode/pdvenv/bin/fastmcp run "$PWD/backend/mcp_server.py"

# UI
# npm run dev / npm run build inside frontend/ (see frontend/README.md)

# Sandbox demo (needs API on :8000 with TYPESAFE_API_KEY)
/tmp/opencode/pdvenv/bin/python pulsedesk-os/sandbox/run_demo.py
```
