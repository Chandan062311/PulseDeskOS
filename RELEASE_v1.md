# PulseDesk OS v1.0 — Release Notes

PulseDesk OS v1.0 is a support-queue reference application built around one clear
boundary: Python owns workflow and TypeSafe Jev supplies narrow judgments.

## Shipped

### Ticket pipeline

- Nine-question Jev triage for route, memory need, credentials, sender mismatch,
  unexpected reward, refund intent, PII, urgency, and frustration.
- Deterministic gates produce `auto_route`, `human_review`, or `quarantine_spam`.
- Five registered handlers: `it_access`, `bug_report`, `billing`, `hr_policy`, and `other`.
- Offline triage remains available without a key; live orchestration reports a clear
  503 when `TYPESAFE_API_KEY` is unavailable.

### Memory and verification

- Tenant-scoped SQLite memory backend with BM25 candidate search.
- Jev reranking for relevance, contradiction, prompt injection, and PII signals.
- Tenant ID is mandatory for deletion.
- Live verification checks drafted replies against cited evidence.
- Resolved auto-routed tickets can be captured as decision memories.

### Interfaces and packaging

- FastAPI REST API with OpenAPI docs at `/docs`.
- Vite + React console with Triage, Pipeline, Review, and System views.
- Claude Code plugin with three skills, reviewer agent, and five MCP tools.
- Docker Compose, Render, and Vercel deployment configuration.

## Configuration

Behavior is configured in [`config.yaml`](config.yaml): routing confidence, spam weights,
memory filters, handler thresholds, verification, and orchestration settings. Secrets
belong in `.env` or the hosting provider's environment settings.

## Verification

The repository CI workflow runs:

- `ruff check` and `ruff format --check`
- strict `mypy` for the backend
- the full pytest suite
- plugin manifest validation and secret scanning
- a production frontend build

Run the same local checks with `make test`, `make build-ui`, and `make secrets`.

## Known limitations

- PII is detected and gated, but the current pipeline does not redact raw ticket text
  before sending it to Jev.
- Large memory documents are not chunked before recall.
- Recall responses do not yet expose per-candidate drop reasons.
- The frontend review queue is session-backed; a durable backend audit log is future work.

## Try the demo

With the API running and a live key configured:

```bash
python sandbox/run_demo.py
```

The script runs five representative tickets and writes its ignored JSON output to
`sandbox/report.json`.
