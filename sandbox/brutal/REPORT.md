# Brutal sandbox sweep — findings → repairs

4 adversarial agents, 60+ cases, 0 crashes (no 500 on any bad input).
Full per-agent logs: `brutal/triage.md`, `brutal/memory.md`,
`brutal/platform.md`, `brutal/contracts.md`.

## Fixed in code (+ regression tests)

| # | Shortcoming | Repair |
|---|---|---|
| mem S1 | Tenant-unscoped delete (cross-tenant delete by bare id) | `DELETE …?tenant_id=` enforced in SQL; mismatch → `false`. Test: `test_delete_is_tenant_scoped` |
| plat S1 | Top-level wrappers silently ignored unknown fields | All `main.py` request/response models now `Frozen` (`extra=forbid`). Test: `test_top_level_extra_fields_rejected` |
| mem S3, plat S2 | Unconstrained memory `type` (`banana` stored, coerced later) | `MemoryStoreRequest.type` is `Literal`; MCP `add_memory` raises `ValueError`. Test: `test_store_validates_type_and_text` |
| mem S5 | Empty text accepted | API 422 + MCP `ValueError` (same test) |
| plat S4 | MCP `None` inputs → raw traceback | `_req_str` guards on all 5 tools → `ValueError`. Test: `test_mcp_tool_input_guards` |
| tri S5 | Null sender 422 vs missing-sender defaults | `NonNullStr` coerces null → `""`. Test: `test_null_sender_coerced_to_defaults` |
| tri S2 | PII blind spot (no signal, raw PII to Jev) | 9th question `pii_detected` → `TriageResult.pii_detected`; live SSN+card → **0.99**. UI meter added. Test: `test_pii_signal_flows_through` |
| tri S1 | Empty message conf 0.99 | Mitigated by `other→review` backstop; pinned by test `test_empty_message_reviews_via_other_backstop` |
| tri S3 | Injection drives `refund_requested=0.97` | Quarantine gate suppresses downstream use; pinned by `test_quarantine_wins_over_attacker_refund` |
| con S4 | Band edges undocumented (strict vs inclusive) | Pinned exclusive by `test_spam_band_edges_are_exclusive`; skill + ARCHITECTURE worded exclusive |
| con S3/S5 | Dead config keys; hardcoded handler/verify thresholds | Removed `destructive_confidence_threshold`, `uncertain_floor`; added `handlers.*`, `verify.*` sections wired into `builtins.py`/`verify.py` |
| con S6/S9 | MCP `top_k` divergence; divergent seed docs; stale Jev policy text | MCP uses `orchestrator.SEED_DOCS` + config `bm25_top_k`; `build_triage_state` takes live config |
| con S1/S7/S8/S2 | Docs drift (README table/structure, ARCHITECTURE gates, evals README, skill routes) | README table + structure rewritten; ARCHITECTURE gates rewritten; evals README fixed; triage skill enumerates routes |
| con S1 | `hr_policy` had zero goldens | +2 hr tickets (14 total); count test updated |
| con S10 | UI hardcoded customer context | Plan + open-orders inputs in composer; shared `ticketBody` (Pipeline inherits) |
| mem S7/plat S8 | `recall?live=false` 503 message misleading | Split messages: live-only vs missing-key |
| plat S3 | MCP `limit=0/-1` silently empty | `ValueError` for `limit < 1` |

## Accepted as designed (documented, not changed)

- Dual-intent collapse to single label (Choice is single-label by design).
- Duplicates allowed (no dedup); unknown query params ignored (FastAPI default);
  missing Content-Type 422 wording (framework default); 20-way offline latency
  ~200ms vs 1–2ms sequential (threadpool overhead, zero errors).

## Backlog (mapped, not yet built)

- Pre-Jev PII redaction (signal exists; raw text still reaches Jev).
- 50KB+ doc chunking (BM25 #1 but Jev relevance dilutes below 0.70).
- Dropped-candidate reason codes in recall responses.
- Backend audit log as review-queue source of truth (UI uses session state).

## Post-repair verification

- 40 pytest passed · ruff + format + mypy strict clean · `claude plugin validate` ✔
- Live goldens 14/14 joint (incl. 2 new hr_policy) with 9-question battery, no drift
- Sandbox problem statement 5/5, exit 0 · UI 200 · API ok
