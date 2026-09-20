# Sandbox run — Acme Monday-morning queue

Isolated run: fresh `MEMORY_DB`, tenant `sandbox`, live Jev on all 5 tickets.
Reproduce: `/tmp/opencode/pdvenv/bin/python pulsedesk-os/sandbox/run_demo.py`
(needs the API on :8000 with `TYPESAFE_API_KEY`).

## Problem statement

Monday 09:00 after a deploy weekend: checkout API 500ing (outage), a
double-charged customer, a joiner needing VPN, a "bonus" phish, one vague
"something seems off" report.

## Results (5/5 match expectations)

| Ticket | Route (conf) | Spam | Action | Memory | Verify |
|---|---|---|---|---|---|
| S1 outage | bug_report (1.00) | 0.03 | auto_route, urg 1.00 | 0 hits (needs_memory below 0.60) | needs_review |
| S2 billing | billing (1.00) | 0.04 | auto_route | 1 hit: refund policy rel 0.87 | needs_review |
| S3 VPN | it_access (1.00) | 0.04 | auto_route | 1 hit | needs_review |
| S4 phish | other (1.00) | 0.86 | quarantine_spam | skipped | needs_review |
| S5 vague | other (1.00) | 0.04 | human_review | skipped | needs_review |

Review queue: S4-phish, S5-vague. Full JSON: `report.json`.

## Bugs the sandbox caught (both fixed + regression-tested)

1. **SQLite threading crash** — singleton connection created in one thread,
   used in uvicorn workers → 500s. Fix: `check_same_thread=False` + lock
   in `backend/memory_backends/sqlite.py`. Test: `test_sqlite_backend_is_thread_safe`.
2. **Confident "other" auto-routed nowhere** — vague ticket got `other/1.00`
   → `auto_route` to a catch-all with no owning team. Fix: `other` always
   reviews (`routing.other_always_review`, default true, in `config.yaml`).
   Test: `test_other_route_always_reviewed`. Matches golden evals
   (`ambiguous-*` expect `other/human_review`).

## Open tuning notes (not bugs)

- S1 outage retrieved 0 memory hits: `needs_memory` was below threshold for
  that wording. Consider lowering `needs_memory_threshold` (0.60) or
  rewording, evaluated against the golden set.
- Verify returns `needs_review` on good drafts (calibrated caution) — tune
  `verify` policy once reply templates stabilize.
