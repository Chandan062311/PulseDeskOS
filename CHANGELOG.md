# Changelog

Note on sourcing: the repo's reports (`sandbox/report.md`,
`sandbox/brutal/REPORT.md`) do not label which change landed in which
pre-1.0 version. All entries below are dated 2026-09-20 (release day).
v0.1–v0.3 groupings are **inferred** from the current `README.md`,
`ARCHITECTURE.md`, `config.yaml`, and report contents, and are marked as
such. No test counts or metrics are stated beyond what the reports source.
Omitted where sourcing is absent.

## v1.0 — 2026-09-20

Release hardening + documentation freeze.

- Full pipeline verified end to end: triage (9 questions:
  `route`/`needs_memory`/`requests_credentials`/`sender_identity_mismatch`/
  `unexpected_reward`/`refund_requested`/`pii_detected`/`urgency`/
  `frustration`) → gated action (`auto_route` / `human_review` /
  `quarantine_spam`) → registry dispatch → conditional Req2 recall → verify
  (`sandbox/report.md`: Monday-morning queue 5/5 match expectations).
- Brutal-sweep repairs landed with regression tests (per
  `sandbox/brutal/REPORT.md`): tenant-scoped delete; `Frozen`
  (`extra="forbid"`) top-level models; `Literal` memory `type` + empty-text
  422; MCP input guards (`_req_str`, `limit < 1`); null-sender coercion;
  `pii_detected` 9th question; `other → review` backstop; exclusive spam-band
  edges; dead config keys removed (`destructive_confidence_threshold`,
  `uncertain_floor`) with `handlers.*` / `verify.*` sections wired in
  (`builtins.py` reads `handlers.*` via `load_config`, `verify.py` reads
  `verify.needs_review_threshold`); MCP `top_k` / seed-doc / triage-state
  consistency fixes; docs drift fixes (README table + structure, ARCHITECTURE
  gates, evals README, triage skill routes); +2 `hr_policy` goldens
  (14 total); composer plan + open-orders inputs; split
  `recall?live=false` 503 messages.
- Verification per reports: adversarial sweep with 0 crashes (no 500 on bad
  input); 40 pytest passed + `ruff` + format + `mypy` strict clean;
  `claude plugin validate` ✔; live goldens 14/14 joint; sandbox demo exit 0,
  UI 200, API ok. These are the only counts claimed; per-run detail lives in
  the reports.
- Known limitations carried as backlog — see `RELEASE_v1.md`
  (pre-Jev PII redaction, 50KB+ chunking, dropped-candidate reason codes,
  backend audit log as review-queue source of truth).

## v0.3 — 2026-09-20 (inferred sequencing)

- Memory platform (sourced: `config.yaml` comment "v0.3 memory-platform"):
  `memory.auto_capture_resolved: true` — resolved `auto_route` tickets
  stored back as `decision` memories.
- Plugin `v0.3.0` (sourced: `.claude-plugin/plugin.json` `name: pulsedesk,
  v0.3.0`, mirrored in `README.md`): `skills/triage`, `skills/orchestrate`,
  `skills/memory` + reviewer agent + bundled MCP server (5 tools:
  `triage_ticket`, `recall_memory`, `add_memory`, `list_memories`,
  `verify_response`).
- (Inferred) PII 9th question, strict request/response models, and
  tenant-scoped delete hardening plausibly landed across late v0.3 / v1.0
  brutal-sweep fixes — exact version boundary unsourced, see v1.0 list.

## v0.2 — 2026-09-20 (inferred)

- (Inferred) Memory recall path (BM25 shortlist + Jev rerank) and verify
  step composed into the orchestrate chain
  (triage → recall → dispatch → draft → verify); seed-default-docs flow.
  Grouping inferred from `ARCHITECTURE.md` / `backend/main.py` structure;
  version boundary unsourced.

## v0.1 — 2026-09-20 (inferred)

- (Inferred) Initial triage + ingest API with config-gated actions and the
  handler registry. Grouping inferred; details omitted for lack of
  version-specific sourcing.
