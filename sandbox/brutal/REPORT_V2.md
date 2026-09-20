# Re-audit (v2) — shipped state, 4 agents, repairs, verification

Date: 2026-09-20. Scope: everything since REPORT.md, esp. auth gate, WAL +
workers, backup/smoke scripts, plugin packaging, RELEASE/CHANGELOG, UI console.
Per-agent logs: `v2-auth.md`, `v2-data.md`, `v2-release.md`, `v2-live.md`.

## Agent verdicts

| Agent | Result |
|---|---|
| A auth + security | PASS — 10/10 routes 401 w/o key, 401 wrong key, 0×500, query-param keys rejected, /docs gated, 20/20 parallel clean |
| B data + pipeline | 16/16 PASS — all v1 fixes hold; tenant delete, validation, pii 0.99/0.03, seed idempotent, auto-capture present |
| C release artifacts | **FAIL** — 23/24 claims pass; 4 doc falsehoods (fixed below) |
| D live behavior | PASS — goldens 14/14, sandbox 5/5, injection held, PII 0.99, zero 500s |

## Repaired (with regression tests)

1. **Rate limiting** (A-S2): sliding-window 120/min/IP, 429 + Retry-After
   (`PULSEDESK_RATE_LIMIT` tunable). Tests: 429 + header.
2. **Constant-time key compare** (A-S1): `hmac.compare_digest`.
3. **Fail-open visibility** (A-S3): startup lifespan logs auth posture
   (`auth enforced` verified in prod logs); `.env` chmod 600 (A-S4).
4. **Tenant-scoped delete mandatory** (B residual): `tenant_id` required (422
   when missing/empty); mismatch → `false`. Tests updated + added.
5. **Honest draft evidence line** (B-2): distinguishes recall-ran-empty from
   recall-skipped. Tests pinned.
6. **Release-doc falsehoods** (C-1..4): 503 wording scoped to true-503 routes;
   handlers row = `builtins.py` 5 classes; contracts = schemas + main models;
   REPORT/RELEASE counts → 55; ARCHITECTURE gate rewrite (correct keys,
   exclusive edges, dead keys documented as removed).
7. **Sandbox script hygiene**: `.env` autoload (demo works with clean env),
   dev-key default documented, ruff-clean sandbox/.

## Accepted / backlog (unchanged from v1 unless noted)

- Empty-message conf 0.99 (backstop holds; test-pinned), dual-intent collapse,
  no dedup, PII-to-Jev unredacted, 50KB chunking, drop-reason codes,
  session-state review queue, confidence saturation (13/14 goldens at 1.00 —
  evals need near-boundary tickets).
- New backlog: near-boundary golden tickets (0.75 conf / 0.40–0.60 spam);
  benchmark alerting on the R1 table.

## Post-repair verification

- 55 pytest passed · ruff + format clean (backend/tests/sandbox) · mypy strict
  clean (20 files) · `claude plugin validate` ✔
- Live goldens 14/14 · sandbox demo 5/5 exit 0 · smoke PASS (incl. 401 gate)
  · UI 200 · API ok · docker images `pulsedesk-os:1.0` + `pulsedesk-ui:1.0`
  built, container serves with gate enforced
- git: clean tree, 3 commits, no secrets/db tracked
