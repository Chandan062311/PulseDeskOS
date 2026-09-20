# Auditor B (data + pipeline) — v2 re-audit findings

Date: 2026-09-20. Target: live API `http://localhost:8000` via
`/tmp/opencode/pdvenv/bin/python` (urllib, header `X-API-Key: dev-key`).
Source was only read, never modified. Tenant prefix `v2b-`
(`v2b-a`, `v2b-wrong`, `v2b-seed`, `v2b-conc`, `v2b-auto`, `v2b-orchfresh`).
All v2b tenants left at count 0 after cleanup (verified via
`GET /v1/memory/count` per tenant).
Verdict rule: FAIL = 500, isolation break, validation miss, missing `pii_detected`
field, auto-capture absent. Else PASS.

## Findings table

| # | Case | Status / output | Verdict + reason |
|---|------|-----------------|------------------|
| 1 | tenant-scoped delete: store in `v2b-a`, `DELETE ?tenant_id=v2b-wrong` | 200 `{"deleted":false}` | PASS — cross-tenant delete refused |
| 2 | same id, `DELETE ?tenant_id=v2b-a` | 200 `{"deleted":true}` | PASS — owner-tenant delete works |
| 3 | store `type:"banana"` | 422 `literal_error: Input should be 'ticket', 'doc' or 'decision'` | PASS — fixed vs v1 (was 200, stored raw) |
| 4 | store empty text `""` and `"   "` | 422 `{"detail":"text must be non-empty."}` both | PASS — fixed vs v1 (was 200) |
| 5 | triage sender `"email": null`, `?live=true` and `?live=false` | 200 both (live: `it_access/auto_route`; offline: `other/human_review`) | PASS — fixed vs v1 (was 422); null coerces to `""` per `NonNullStr` |
| 6 | store with top-level extra field `extra_field` | 422 `extra_forbidden` | PASS — `Frozen(extra="forbid")` enforced |
| 7 | triage with top-level extra field `bogus` | 422 `extra_forbidden` | PASS — same enforcement on triage |
| 8 | triage PII message (SSN + card) `?live=true` | 200, `pii_detected=0.99`, `billing/human_review` | PASS — field present, high on PII |
| 9 | triage clean VPN message `?live=true` | 200, `pii_detected=0.03`, `it_access/auto_route` | PASS — field present, low on clean text |
| 10 | triage empty message `""` `?live=true` | 200 `other/human_review` (route_conf 0.99) | PASS — safe action; overconfidence noted, see S3 |
| 11 | `POST /v1/memory/recall?live=false` | 503 `{"detail":"Memory recall is live-only: retry without live=false."}` | PASS — live-only wording as expected (no 500) |
| 12 | seed twice (`v2b-seed`) | first `{"seeded":3}`, second `{"seeded":0}`, count 3 | PASS — idempotent |
| 13 | concurrent 10x store + 10x recall, same tenant (`v2b-conc`) | 10/10 stores 200, 10/10 recalls 200, zero 500s, count 10 | PASS — thread-safe under concurrency |
| 14 | `POST /v1/verify` empty evidence (and empty reply+evidence) | 200 `{"supported":0.0,"confidence":1.0,"verdict":"needs_review"}` both | PASS — no 500, safe verdict |
| 15 | orchestrate `seed=false` on fresh tenant (`v2b-orchfresh`, vague `hello?` ticket) | 200 `other/human_review`, `captured_memory_id=""`, count 0, list `[]` | PASS — no seeding, no capture on non-auto_route |
| 16 | orchestrate auto_route ticket (VPN/SSO lockout, `seed=true`, `v2b-auto`) | 200 `it_access/auto_route`, `captured_memory_id="32ed023d…"`, list shows 3 seed docs + 1 `decision` memory (`Resolved it_access: …`) | PASS — auto-capture present |

Counts: 16/16 PASS. Zero 500s across all probes.

## SHORTCOMINGS

1. **Unscoped `DELETE` (no `tenant_id`) still deletes cross-tenant — residual S1 from v1.**
   Scoped deletes are now enforced (cases 1–2), but `DELETE /v1/memory/{id}`
   with no `tenant_id` falls back to `DELETE WHERE id = ?`
   (`backend/main.py:262-268` → `sqlite.py:94-113`) and removes another
   tenant's row. Repro: `POST /v1/memory/store {"tenant_id":"v2b-a",…}` →
   `DELETE /v1/memory/{id}` (no query param) → `{"deleted":true}` (observed).
   By-code-design fallback, but any caller that omits `tenant_id` bypasses
   isolation; consider requiring `tenant_id` (422 when absent). Severity: minor
   given scoped path works, but flagging because v1 S1 was an isolation gap.
2. **Orchestrate draft mislabels empty evidence (minor wording).**
   In case 16, `needs_memory=0.89` (above the 0.60 recall threshold) yet
   `memory_hits=[]`, and the draft still prints
   `"Evidence: none retrieved (needs_memory below threshold)."`
   (`backend/orchestrator.py:99-106` — static string whenever hits are empty).
   The parenthetical is factually wrong when recall ran but rerank kept nothing.
   Repro: case-16 response shows `needs_memory 0.89` alongside that line.
   Cosmetic; no pipeline effect.
3. **Overconfident route confidence on vacuous input (carried over from v1 S1).**
   Empty message returns `route_confidence 0.99` (`other`); only the
   `other_always_review` backstop keeps it in `human_review` (case 10).
   Calibration on empty input still broken. Repro:
   `{"ticket":{"subject":"Empty body test","message":"",…}}` → `other` @ 0.99.
4. **Offline triage carries zero PII signal (by design, noted for completeness).**
   The same PII message via `?live=false` returns `pii_detected=0.0`
   (midpoint mock), so offline mode cannot discriminate PII. Expected given
   the mock, but downstream consumers must not trust offline `pii_detected`.

(End of file)
