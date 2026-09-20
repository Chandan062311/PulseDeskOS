# PulseDesk OS — Evals

## golden-tickets.json

Each entry is a labeled ticket (14 total: all five routes, all three actions):

```json
{
  "id": "billing-duplicate-charge",
  "ticket": {"subject": "...", "message": "...", "sender": {"email": "..."}},
  "customer": {"plan": "enterprise", "open_orders": ["INV-2041"]},
  "expected_route": "billing",
  "expect_action": "auto_route"
}
```

Field names are `expected_route` / `expect_action` (no confidence bounds —
judge those from the confidence plots below, not per-ticket).

Cover all five routes (`it_access`, `bug_report`, `billing`, `hr_policy`,
`other`), all three actions (`auto_route`, `human_review`,
`quarantine_spam`), and the boundary bands (spam 0.40–0.60 uncertain
exclusive edges, route confidence near 0.75).

## Confidence plots

Run the eval suite (backend/eval agents) to produce, per ticket: predicted
`route`, `route_confidence`, `spam_risk`, `action`. Plot:

1. Predicted `route_confidence` histogram split by correct vs misrouted.
   The overlap region sets `routing.topic_confidence_threshold`.
2. `spam_risk` scatter (expected spam vs ham). The gap between the clusters
   sets `spam.quarantine_threshold` and the `uncertain_low/high` review band.
3. Action confusion matrix (expected vs predicted `auto_route` /
   `human_review` / `quarantine_spam`).

## Tuning thresholds

1. Move a threshold in `config.yaml` only (never in code).
2. Re-run `pytest` plus the eval suite.
3. Accept a change when misroutes above the auto-route line go down without
   pushing clearly good tickets into `human_review`.

Defaults: topic 0.75, spam quarantine 0.60 (uncertain band 0.40–0.60,
exclusive edges), memory keep 0.70 / drop 0.30 / contradict 0.60,
needs_memory 0.60. See `ARCHITECTURE.md` for gate semantics.
