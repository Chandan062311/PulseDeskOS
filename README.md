# PulseDesk OS

Enterprise productivity orchestrator powered by TypeSafe Jev (System One).

## Vision

Code owns the workflow. Jev owns the judgments.

PulseDesk routes support tickets deterministically: plain Python composes gates,
thresholds, and handler dispatch. All probabilistic decisions (triage, memory
relevance, verification) are delegated to TypeSafe Jev System One requests that
return typed probabilities. No ad-hoc heuristics in handlers, no LLM string
parsing in core logic.

- Req1 (triage): one Jev call answers 9 questions per ticket — route, route
  confidence, spam risk, urgency, frustration, needs-memory, refund-requested,
  pii-detected, plus supporting rationale.
- Req2 (memory): BM25 shortlist from a pluggable store, Jev reranks for
  relevance / contradiction / injection / PII.
- Verify: Jev judges whether a draft reply is supported by cited evidence.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env and set TYPESAFE_API_KEY (get one at https://console.typesafe.ai/keys)
uvicorn backend.main:app --reload
pytest
```

Requires Python >= 3.11.

## API

Base: `http://localhost:8000`. All contracts are frozen Pydantic models in
`backend/schemas.py`.

| Method | Path               | Input              | Output              | Description                                  |
|--------|--------------------|--------------------|---------------------|----------------------------------------------|
| GET    | `/healthz`         | —                  | `{"status":"ok"}`   | Liveness check                               |
| POST   | `/v1/triage`       | `Ticket`           | `TriageResult`      | Req1: Jev 9-question triage + gated action   |
| POST   | `/v1/ingest`       | `Ticket`           | `IngestResponse`    | Triage, then registry dispatch               |
| POST   | `/v1/orchestrate`  | ticket+tenant      | `OrchestrateResponse` | Full pipeline: triage→recall→dispatch→verify |
| POST   | `/v1/memory/store` | text               | `{id}`              | Store a tenant memory doc                    |
| POST   | `/v1/memory/seed`  | `?tenant_id=`      | `{seeded}`          | Idempotent default policy docs               |
| POST   | `/v1/memory/recall`| query              | `list[MemoryHit]`   | BM25 shortlist + Jev rerank (Req2)           |
| GET    | `/v1/memory/list`  | `?tenant_id=&limit=` | `[{id,text,type}]` | Newest-first tenant memories                 |
| GET    | `/v1/memory/count` | `?tenant_id=`       | `{count}`           | Tenant memory size                           |
| DELETE | `/v1/memory/{id}`  | `?tenant_id=` (optional) | `{deleted}`   | Delete by id, tenant-scoped when given       |
| POST   | `/v1/verify`       | draft + evidence   | `VerifyResult`      | Support verdict for a draft reply            |

Live Jev routes (`orchestrate`, `memory/recall`, `verify`) return **503
with a clear message** when `TYPESAFE_API_KEY` is missing. `triage`/`ingest`
fall back to a neutral offline mock without `?live=true`. Every response
carries `X-Request-Id` and structured latency logs.

## Production run

Segregation: one secret in `.env` (the Jev key — never git), data in the
`pddata` volume, code in images. Per-IP rate limiting (120/min) guards the
live Jev routes against runaway bills.

```bash
cp .env.example .env  # set TYPESAFE_API_KEY only
docker compose up --build -d   # api :8000 (4 workers, WAL sqlite) + ui :8080
./scripts/smoke.sh
./scripts/backup.sh ./backups  # online snapshot via MEMORY_DB
docker build -t pulsedesk-os:1.0 .            # verified 216MB
docker build -t pulsedesk-ui:1.0 ./frontend   # verified 63MB
# or: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

CI (`.github/workflows/ci.yml`) runs `ruff check`, `mypy backend`
(strict), `pytest`, and the Vite build on every push.

`TriageResult.action` is one of `auto_route`, `human_review`,
`quarantine_spam`, derived from `config.yaml` thresholds (see
`ARCHITECTURE.md`).

## Claude Code plugin (Superpowers-style)

This repo **is** the plugin — manifest + skills + agent + bundled MCP server:

```
.claude-plugin/plugin.json   # name: pulsedesk, v0.3.0
skills/triage/SKILL.md       # /pulsedesk:triage
skills/orchestrate/SKILL.md  # /pulsedesk:orchestrate
skills/memory/SKILL.md       # /pulsedesk:memory
agents/reviewer.md           # review-queue worker agent
.mcp.json                    # bundled MCP (5 tools: triage, recall, add, list, verify)
```

Test locally, install from a marketplace once pushed to GitHub
(`<owner>/<repo>` below = this repo's GitHub path):

```bash
claude --plugin-dir .                              # try it: /pulsedesk:triage …
claude plugin validate .                           # ✔ Validation passed
/plugin marketplace add <owner>/<repo>             # in Claude Code
/plugin install pulsedesk@pulsedesk-marketplace
```

Prerequisite for the MCP server: `pip install -e ".[dev]"` (fastmcp,
typesafe-sdk) and `TYPESAFE_API_KEY` for live Jev routes.

## MCP usage (without the plugin)

Five tools (`triage_ticket`, `recall_memory`, `add_memory`, `list_memories`,
`verify_response`) for any MCP host:

```bash
make mcp                                            # stdio server on PATH python
claude mcp add pulsedesk -- python -m backend.mcp_server   # from repo root
```

Cursor / VS Code / Codex: point your MCP config at
`python -m backend.mcp_server` with cwd = repo root (stdio transport).

`backend/mcp_server.py` wraps the same `Ticket`,
`TriageResult`, `MemoryHit`, `VerifyResult` schemas (5 tools: triage_ticket,
recall_memory, add_memory, list_memories, verify_response). No duplicate types.

## Stitch UI status

`frontend/` is a working Vite+React ops console (sidebar nav: Triage /
Pipeline / Review / System; `npm run dev`, `npm run build` verified).
Production screens are generated via Stitch MCP — see
`frontend/README.md` and `frontend/stitch-prompts.md` (3 copy-paste prompts:
Inbox dashboard, Triage detail, Review queue).

## Evals + thresholds

`evals/golden-tickets.json` holds 14 labeled tickets with expected route and
action. `evals/README.md` explains how each ticket maps to confidence plots
and how to tune `config.yaml` thresholds (`topic_confidence_threshold`,
spam weights, memory gates) without changing code.

## Project structure

```
pulsedesk-os/
  README.md            # this file
  ARCHITECTURE.md      # flow, components, gating, extensibility rules
  LICENSE              # MIT
  .gitignore
  config.yaml          # all tunable thresholds (change here, not in code)
  .env.example         # TYPESAFE_API_KEY template
  pyproject.toml
  backend/
    schemas.py         # frozen contracts (single source of truth)
    registry.py        # Handler / MemoryBackend registries + register()
    jev_client.py      # all Jev calls go through here
    handlers/          # builtins.py: 5 handlers (extend with new files)
    memory_backends/   # SQLite now, Postgres/supermemory later
    main.py            # FastAPI app: triage/ingest/orchestrate/memory/verify
    mcp_server.py      # FastMCP tools (triage/recall/add/list/verify)
    orchestrator.py    # triage→recall→dispatch→draft→verify chain
  frontend/
    README.md          # run guide + design tokens + Stitch workflow
    stitch-prompts.md  # 3 copy-paste screen prompts
    package.json       # Vite+React console (npm run dev/build)
    src/               # App shell + api.ts + components/
  evals/
    README.md          # golden tickets -> plots -> threshold tuning
    golden-tickets.json# 14 labeled tickets (all 5 routes, 3 actions)
  skills/              # plugin skills: triage, orchestrate, memory
  agents/              # reviewer agent
  .claude-plugin/      # plugin manifest (name: pulsedesk)
  .mcp.json            # bundled MCP server config
  sandbox/             # demo + brutal sweep findings + reports
  tests/               # pytest suite
```

## Contributing

- Add a handler = new file under `backend/handlers/` + `register()` it.
  Never edit triage core to add a route.
- Change shapes in `backend/schemas.py` (domain contracts) or the
  request/response models in `backend/main.py` + bump the `/v1` API version.
  Never use ad-hoc dicts across handler boundaries.
- Tune behavior in `config.yaml`, not in code.
- All Jev calls go through `backend/jev_client.py`.
- Keep models frozen (`frozen=True, extra="forbid"`).

## License

MIT. See `LICENSE`.
