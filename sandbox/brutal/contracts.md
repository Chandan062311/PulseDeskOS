# Adversary D — contracts / docs / UI / golden-eval sweep (READ-ONLY source)

Date (UTC): 2026-09-20 · Repo: `/home/asus/Typesafe/pulsedesk-os` · Python: `/tmp/opencode/pdvenv/bin/python` · API: `http://localhost:8000`
Method: read-only sweep of source; only file written is this one.

## 1. Skills vs code (tool names / thresholds / routes)

**Tool names — PASS (no phantom tools).**
- `backend/mcp_server.py` registers exactly 5 tools: `triage_ticket`, `recall_memory`, `add_memory`, `list_memories`, `verify_response` (lines 159–163).
- `skills/triage/SKILL.md` refs `triage_ticket` — exists.
- `skills/orchestrate/SKILL.md` refs `triage_ticket`, `recall_memory`, `verify_response` — all exist.
- `skills/memory/SKILL.md` refs `recall_memory`, `verify_response`, `add_memory`, `list_memories` — all exist. Its `suggest()` recipe uses `typesafe_sdk.Choice/Noul` directly, not MCP — not a drift.
- HTTP routes cited in skills all exist in `backend/main.py`: `POST /v1/orchestrate`, `POST /v1/memory/store`, `POST /v1/memory/recall`, `GET /v1/memory/list`, `DELETE /v1/memory/{id}`, `GET /v1/memory/count`.

**Thresholds quoted — NUMBERS match `config.yaml`, semantics partly don't (see SHORTCOMINGS).**
- triage skill: `spam_risk >= 0.60` = `spam.quarantine_threshold 0.60`; `0.40–0.60` = `uncertain_low/high 0.40/0.60`; `route_confidence < 0.75` = `routing.topic_confidence_threshold 0.75`; `other → review` = `other_always_review: true`. Numerically exact.
- orchestrate skill: `needs_memory >= 0.60` = `orchestration.needs_memory_threshold 0.60`; `contradicts >= 0.60` = `memory.contradict_flag_threshold 0.60`; `has_injection >= 0.30` = `memory.drop_injection_threshold 0.30`. Exact.
- memory skill: `relevance >= 0.70 / injection >= 0.30 / contradicts >= 0.60 / top_k = 30` = `memory.*` values; `gate 0.30 / fits 0.30 / shortlist 3` = `skill_suggest.*`. Exact.
- reviewer.md: `needs_memory >= 0.60`, `has_injection >= 0.30`, `contradicts >= 0.60`. Exact.

**Routes — PASS where enumerated, incomplete in one place.**
- `Route` enum (`backend/schemas.py:20-27`): `it_access | bug_report | billing | hr_policy | other`.
- orchestrate skill line 22 and `agents/reviewer.md` line 17–18 enumerate all 5 exactly. Match.
- triage skill only ever names `other` (line 20); never enumerates the other four. Not wrong, but incomplete as a routing contract.

## 2. Plugin packaging

- `agents/reviewer.md` line 4 `tools:` = `mcp__plugin_pulsedesk_pulsedesk__recall_memory, mcp__plugin_pulsedesk_pulsedesk__verify_response` — full `mcp__plugin_<plugin>_<server>__<tool>` form, both tools exist in `mcp_server.py`. **PASS.**
- `.mcp.json` `args: ["${CLAUDE_PLUGIN_ROOT}/backend/mcp_server.py"]` — uses `${CLAUDE_PLUGIN_ROOT}` and `args[0]` ends with `backend/mcp_server.py`. **PASS.** (`command: python3`; tests assert the same in `tests/test_plugin.py:37-43`.)
- `.claude-plugin/plugin.json` is valid JSON with `name: "pulsedesk"`, non-empty `description`, `version: "0.3.0"`. **PASS** (also asserted by `tests/test_plugin.py:14-18`).

## 3. Golden eval — 12/12 live `POST /v1/triage?live=true` (route AND action)

Ran 2026-09-20 against live API (server-side `TYPESAFE_API_KEY`; local shell has none, live still returned 200s). Compared `route` AND `action` vs `expected_route` / `expect_action`.

| # | id | expected (route/action) | live (route/action) | conf / spam | match |
|---|---|---|---|---|---|
| 1 | billing-duplicate-charge | billing / auto_route | billing / auto_route | 1.00 / 0.032 | ✅ |
| 2 | billing-invoice-copy | billing / auto_route | billing / auto_route | 1.00 / 0.026 | ✅ |
| 3 | billing-plan-downgrade | billing / auto_route | billing / auto_route | 1.00 / 0.029 | ✅ |
| 4 | billing-proration | billing / auto_route | billing / auto_route | 1.00 / 0.026 | ✅ |
| 5 | it-vpn-access | it_access / auto_route | it_access / auto_route | 1.00 / 0.026 | ✅ |
| 6 | it-password-reset | it_access / auto_route | it_access / auto_route | 1.00 / 0.064 | ✅ |
| 7 | bug-500-outage | bug_report / auto_route | bug_report / auto_route | 1.00 / 0.033 | ✅ |
| 8 | bug-csv-export | bug_report / auto_route | bug_report / auto_route | 1.00 / 0.025 | ✅ |
| 9 | spam-password-reward | other / quarantine_spam | other / quarantine_spam | 0.98 / 0.929 | ✅ |
| 10 | spam-ceo-giftcard | other / quarantine_spam | other / quarantine_spam | 1.00 / 0.751 | ✅ |
| 11 | ambiguous-vague | other / human_review | other / human_review | 1.00 / 0.033 | ✅ (`route other has no owning team; review`) |
| 12 | ambiguous-mixed | other / human_review | other / human_review | 0.93 / 0.033 | ✅ (`route other has no owning team; review`) |

**Accuracy: 12/12 route (100%), 12/12 action (100%), 12/12 joint (100%).**
Caveats: 11 of 12 confidences are exactly 1.00 (only #12 is 0.93) — the eval passes but exercises no near-threshold (`≈0.75`) or spam-band (`0.40–0.60`) boundary; `hr_policy` has zero tickets (see S1).

## 4. Frontend

- `npm run build` in `pulsedesk-os/frontend`: **PASSES** — `vite v6.4.3`, 33 modules, `dist/index.html + assets/index-*.js/css` built in ~562ms.
- `curl :5173` (dev server already running, PID 395723): **200**, returns `<!doctype html>…<title>PulseDesk OS — Triage Console</title>`.
- `src/api.ts` `SAMPLES` (5) each through live `POST /v1/triage?live=true`, 2026-09-20 — **no 500s**:

| sample | live route / action | conf / spam |
|---|---|---|
| dup-charge | billing / auto_route | 1.00 / 0.062 |
| outage | bug_report / auto_route | 1.00 / 0.036 |
| vpn | it_access / auto_route | 1.00 / 0.036 |
| phish | other / quarantine_spam | 1.00 / 0.861 |
| vague | other / human_review | 1.00 / 0.042 |

All HTTP 200.

## 5. README / ARCHITECTURE vs reality

**README API table (`README.md:41-50`) vs `backend/main.py`:**
- Every *documented* route exists: `GET /healthz` (165), `POST /v1/triage` (176), `POST /v1/ingest` (190), `POST /v1/orchestrate` (253), `POST /v1/memory/store` (205), `POST /v1/memory/seed` (212), `POST /v1/memory/recall` (218), `POST /v1/verify` (245). **PASS one direction.**
- Every *real* route is documented: **FAIL** — `GET /v1/memory/list` (226), `DELETE /v1/memory/{mem_id}` (233), `GET /v1/memory/count` (239) exist but are absent from the table (they *are* documented in `skills/memory/SKILL.md:12-14`, so docs contradict each other).

**README project structure (`README.md:126-154`) — STALE in 3 spots:**
- Lists `backend/mcp.py`; real file is `backend/mcp_server.py`.
- Lists `skill/SKILL.md` (singular); real layout is `skills/{triage,orchestrate,memory}/SKILL.md`.
- "Frontend is stub-only … No build step required yet" (§Stitch UI status, structure note `package.json # stub (no build required)`, `src/App.tsx # placeholder`) contradicts `frontend/` reality: full console (`App.tsx` shell + `components/{TriagePanel,PipelinePanel,ReviewQueue,SystemPanel,ui}.tsx`, `api.ts` typed client) with working `npm run build` → `dist/` (verified above). `frontend/README.md` itself says `npm run build # verified: vite build succeeds -> dist/`.
- Plugin block (`README.md:83`) describes `.mcp.json` as "(triage_ticket, recall_memory, verify_response)" — omits bundled `add_memory`, `list_memories`.

**ARCHITECTURE.md component table (lines 26–38) — file names PASS, gate semantics FAIL:**
- All named files exist: `schemas.py`, `jev_client.py`, `registry.py`, `handlers/`, `memory_backends/`, `main.py`, `orchestrator.py`, `mcp_server.py`, `.claude-plugin/plugin.json`, `skills/`, `agents/`, `.mcp.json`, `config.yaml`, `frontend/`, `evals/`.
- But §Confidence gating lines 68–71 misstate the code (see S2): recall gate cited as `memory.keep_relevance_threshold (0.70)`, code uses `orchestration.needs_memory_threshold (0.60)`; "low-relevance (`< drop_injection_threshold`, 0.30)" conflates the relevance gate (0.70) with the injection gate (0.30).
- Lines 62–66 + flow chart present `destructive_confidence_threshold (0.90)` and `uncertain_floor (0.50)` as enforced gates; neither is read by any code (see S3).

## 6. `config.yaml` coverage vs magic numbers in `backend/`

Every *code-read* threshold has a value — the reverse fails: 3 config keys are dead (no reader outside docs), and several live numbers never consult config:

- Dead config (grep over `backend/**/*.py`, zero hits): `routing.destructive_confidence_threshold (0.90)`, `routing.uncertain_floor (0.50)`, `skill_suggest.*` (`gate_threshold 0.30`, `fits_threshold 0.30`, `shortlist_k 3` — only referenced in `skills/memory/SKILL.md` recipe, never imported by code).
- Hardcoded behavior numbers (not from config): `backend/handlers/builtins.py:75` `triage.urgency >= 0.75` (SEV-1/SEV-3); `builtins.py:112` `triage.refund_requested >= 0.5`; `backend/verify.py:24` `_NEEDS_REVIEW_THRESHOLD = 0.5`; `backend/mcp_server.py:106` `recall … top_k=3` (vs config `bm25_top_k: 30` and `orchestration.max_memory_hits: 5` — three different Ks); `mcp_server.py` stub literals `0.5/0.1/0.0/0.25`, `verify_response` stub `0.5, {0.5, 0.25, 0.25}`.
- Mirrored defaults (fallback when config missing — by design, but duplicates config values in code): `triage.py:32-40` (`0.75/0.60/0.40/0.60`, weights `0.45/0.30/0.25`), `memory.py:48-50` (`0.70/0.30/0.60`), `memory.py:148` (`bm25_top_k` fallback `30`), `orchestrator.py:41-42` (`0.60`, `5`). Additionally `triage.py:70-74 build_triage_state["policy"]` embeds these *defaults*, not the live `config.yaml` values, into the Jev state — tuning config does not change what Jev is told the thresholds are.

---

## SHORTCOMINGS (numbered + evidence)

1. **Golden set covers 4 of 5 routes; evals README promises 5 and documents fields that don't exist.** `evals/golden-tickets.json` distribution is billing×4, it_access×2, bug_report×2, other×4, **`hr_policy×0`** (counted 2026-09-20). `evals/README.md` says "Cover all five routes" and shows a schema with `expected_action / min_route_confidence / max_spam_risk`, but the file uses `expect_action` and carries no confidence/spam bounds. No test can regress `hr_policy` routing or the documented bounds.
2. **ARCHITECTURE.md misstates the recall gate (wrong key, wrong value, conflated thresholds).** Lines 68–71: "if `needs_memory >= memory.keep_relevance_threshold` (default 0.70)… low-relevance (`< drop_injection_threshold`, default 0.30)". Code: `orchestrator.py:140-141,183` gates on `orchestration.needs_memory_threshold` (default `0.60`); `memory.py:119` keeps on `relevance >= 0.70` and drops on `injection >= 0.30` — two separate predicates the doc merges into one.
3. **Two documented triage gates are dead config.** `config.yaml` sets `routing.destructive_confidence_threshold: 0.90` and `routing.uncertain_floor: 0.50`; `ARCHITECTURE.md:62-66` and the flow chart describe them as enforced; `rg` over `backend/` finds **zero readers** (only `topic_confidence_threshold`, `quarantine_threshold`, `uncertain_low/high`, `other_always_review` are read in `triage.py:304-335`). `skill_suggest.*` is likewise code-unreferenced.
4. **Boundary semantics differ between docs and code.** Skills/README describe the spam review band as inclusive `0.40–0.60`; code (`triage.py:320,322`) uses strict `uncertain_low < spam < uncertain_high`, so exactly `0.40` → not-band (falls to confidence gate) and exactly `0.60` → quarantine (`>=`). No ticket in the golden set probes either edge (all live spam values were ≤0.064 or ≥0.751).
5. **Business logic hidden in hardcoded literals, violating the repo's own "config.yaml, not code" rule.** `builtins.py:75` (`urgency >= 0.75` SEV boundary), `builtins.py:112` (`refund_requested >= 0.5`), `verify.py:24` (`_NEEDS_REVIEW_THRESHOLD = 0.5`) have no config key; `CONTRIBUTING`/`ARCHITECTURE` ("Tune behavior in config.yaml, not in code", "Code reads them via `load_config()`") is therefore aspirational for these three.
6. **MCP server diverges from the API it claims to wrap.** `mcp_server.py:106` hardcodes `top_k=3` vs API default `top_k=5` (`main.py:75`) vs config `bm25_top_k: 30` vs `max_memory_hits: 5`; `_DEMO_DOCS` (refund-duplicate/VPN-new-hire/… lines 70–74) differ in text and tuple order from `orchestrator.SEED_DOCS` (lines 35–39, `(type, text)` vs `(text, type)`), so MCP-seeded tenants and API-seeded tenants start from different "default policy docs". README further hides 2 of the 5 MCP tools (§5).
7. **README project structure + frontend status are stale.** `backend/mcp.py` → actually `backend/mcp_server.py`; `skill/SKILL.md` → actually `skills/{triage,orchestrate,memory}/SKILL.md`; "stub-only … No build step required yet" → actually a working Vite+React console whose build was verified passing in §4. A newcomer following the structure diagram looks for files that don't exist and dismisses a UI that does.
8. **README API table omits 3 live memory routes.** `GET /v1/memory/list`, `DELETE /v1/memory/{id}`, `GET /v1/memory/count` (main.py:226/233/239) are missing from `README.md:41-50`, though `skills/memory/SKILL.md:12-14` documents them — the two docs disagree on the public surface.
9. **Jev is told stale thresholds.** `build_triage_state` (`triage.py:70-74`) puts `_DEFAULT_*` constants into `state["policy"]` instead of the loaded `config.yaml` values, so an operator who retunes `topic_confidence_threshold` changes the gate but not the policy text Jev reasons over. Either the state should take config or the field should be removed.
10. **Frontend never sends real customer context.** `frontend/src/api.ts:76-86 ticketBody` hardcodes `{plan: "enterprise", open_orders: []}` for every request, so plan/order-sensitive triage (e.g. golden `billing-duplicate-charge` with `open_orders: ["INV-2041"]`) cannot be reproduced from the UI, and UI results are not comparable to eval results.
