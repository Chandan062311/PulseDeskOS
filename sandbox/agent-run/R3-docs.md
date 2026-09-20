# R3-docs — Docs-truth re-audit (read-only scout)

Repo: `/home/asus/Typesafe/pulsedesk-os`. Method: README/ARCHITECTURE/skills/reviewer claims checked line-by-line against `backend/main.py`, `backend/triage.py`, `config.yaml`, `backend/orchestrator.py`, `backend/memory.py`, `backend/mcp_server.py`, `backend/schemas.py`, `.claude-plugin/plugin.json`, `.mcp.json`. No files modified except this one.

## 1. README.md API table vs backend/main.py — CLEAN
Drift list: (empty)
- All 11 documented routes exist in code, and all 11 real routes are documented:
  - `GET /healthz` — README.md:43 vs main.py:167
  - `POST /v1/triage` — README.md:44 vs main.py:177
  - `POST /v1/ingest` — README.md:45 vs main.py:191
  - `POST /v1/orchestrate` — README.md:46 vs main.py:262
  - `POST /v1/memory/store` — README.md:47 vs main.py:206
  - `POST /v1/memory/seed` — README.md:48 vs main.py:215
  - `POST /v1/memory/recall` — README.md:49 vs main.py:221
  - `GET /v1/memory/list` — README.md:50 vs main.py:232
  - `GET /v1/memory/count` — README.md:51 vs main.py:248
  - `DELETE /v1/memory/{id}` — README.md:52 vs main.py:238 (`/v1/memory/{mem_id}`; same route template, param name only differs — cosmetic, not drift)
  - `POST /v1/verify` — README.md:53 vs main.py:254
- Method + path + input/output shapes match in every row (e.g. triage `Ticket→TriageResult`, orchestrate `ticket+tenant→OrchestrateResponse`, recall `query→list[MemoryHit]`).

## 2. ARCHITECTURE.md gates/confidence section vs triage.py + config.yaml + orchestrator.py — CLEAN
Drift list: (empty)
- `spam.quarantine_threshold` 0.60 — ARCHITECTURE.md:58 vs config.yaml:19 vs triage.py:34 (`_DEFAULT_QUARANTINE = 0.60`) and triage.py:326/339 (`>=`).
- Spam weights 0.45 / 0.30 / 0.25 — ARCHITECTURE.md:59-61 vs config.yaml:16-18 vs triage.py:37-41.
- `routing.topic_confidence_threshold` 0.75 (`<` gate) — ARCHITECTURE.md:62-63 vs config.yaml:9 vs triage.py:33,329-330,342.
- Uncertain band strictly between 0.40 and 0.60, edges fall through (0.40 → confidence gate, 0.60 → quarantine via `>=`) — ARCHITECTURE.md:63-65 vs config.yaml:20-21 vs triage.py:342,344 (`uncertain_low < spam_risk < uncertain_high`, quarantine `>= 0.60`).
- `routing.other_always_review` (no owning team) — ARCHITECTURE.md:65-66 vs config.yaml:12 vs triage.py:359-361.
- `orchestration.needs_memory_threshold` 0.60 (`>=` triggers recall) — ARCHITECTURE.md:68-69 vs config.yaml:55 vs orchestrator.py:41,140,183.
- Memory gates `relevance >= 0.70`, `injection >= 0.30` drop, `contradicts >= 0.60` flag-only — ARCHITECTURE.md:69-72 vs config.yaml:25-27 vs memory.py:48-50,119 (`relevance < keep or injection >= drop: continue`; contradicts never a drop reason per memory.py:106-107).
- Dead keys gone as claimed — ARCHITECTURE.md:76-78 vs config.yaml (no `destructive_confidence_threshold`, no `uncertain_floor` anywhere in file).

## 3. skills/*/SKILL.md vs config.yaml + mcp_server.py + Route enum — CLEAN
Drift list: (empty)
- Route set `it_access | bug_report | billing | hr_policy | other` in triage SKILL.md:18, orchestrate SKILL.md:21-22, reviewer-compatible — matches schemas.py:31-35 exactly (5/5, no renames).
- Triage gates (`spam_risk >= 0.60`; strictly between 0.40–0.60; `route_confidence < 0.75`; `other` always reviews) — SKILL.md (triage):19-22 vs config.yaml:9,19-21 vs triage.py:339-361. Exact.
- `needs_memory >= 0.60` recall gate — SKILL.md (orchestrate):18, SKILL.md (memory) implied, reviewer.md:15 vs config.yaml:55 vs orchestrator.py:41. Exact.
- Memory gates `relevance >= 0.70` / `injection >= 0.30` / `contradicts >= 0.60` / `bm25_top_k = 30` — SKILL.md (memory):32-33 vs config.yaml:24-27 vs memory.py:48-50,119. Exact.
- Skill-suggest recipe `gate 0.30 / fits 0.30 / shortlist 3` — SKILL.md (memory):34,40,43,62,77 vs config.yaml:33-36 (`gate_threshold: 0.30`, `fits_threshold: 0.30`, `shortlist_k: 3`). Exact.
- Tools referenced all exist and are registered: `triage_ticket` (mcp_server.py:91,191), `recall_memory` (:118,192), `add_memory` (:147,193), `list_memories` (:164,194), `verify_response` (:177,195). HTTP routes cited in memory SKILL.md:10-14 all exist in main.py (see §1).
- Evidence string `No retrieved evidence.` cited in orchestrate SKILL.md:24 vs orchestrator.py:187 (`"No retrieved evidence."`). Exact.

## 4. agents/reviewer.md + plugin.json + .mcp.json — CLEAN
Drift list: (empty)
- Tool names `mcp__plugin_pulsedesk_pulsedesk__recall_memory`, `mcp__plugin_pulsedesk_pulsedesk__verify_response` (reviewer.md:4) resolve to real functions `recall_memory` (mcp_server.py:118, registered :192) and `verify_response` (mcp_server.py:177, registered :195); server name `pulsedesk` matches `FastMCP("pulsedesk")` (mcp_server.py:45) and `.mcp.json:3`.
- Reviewer thresholds (`needs_memory >= 0.60`, `has_injection >= 0.30`, `contradicts >= 0.60` — reviewer.md:15-16) match config.yaml:55,26,27 and memory.py:48-50. Route list (reviewer.md:17-18) matches schemas.py:31-35.
- plugin.json sanity: `name: pulsedesk`, `version 0.3.0` (plugin.json:2-4) matches README.md:81 (`name: pulsedesk, v0.3.0`); valid JSON, MIT license, homepage present.
- .mcp.json sanity: server `pulsedesk` → `python3 ${CLAUDE_PLUGIN_ROOT}/backend/mcp_server.py` (.mcp.json:3-6); target file exists and is runnable (`mcp.run()` at mcp_server.py:198-199); `env: {}` is valid (API key inherited from environment, as documented in README.md:97).

## Out-of-scope observations (NOT drift against the tasked checks; for owner triage)
- O1: ARCHITECTURE.md:37 Components row says frontend is "Stub only: App.tsx placeholder", but `frontend/src/App.tsx` (83 lines) + `components/` + `api.ts` + `package.json` is a working Vite+React console matching README.md:114-115. Stale ARCH row outside the gates section — suggest updating to "working Vite+React ops console".
- O2: README.md:55-58 lumps `triage?live=true` with 503-on-missing-key routes, but main.py:152-164 falls back to the offline mock for triage/ingest (503 only for orchestrate/recall/verify). The follow-on clause ("offline mocks exist only for triage/ingest") already discloses this; suggest rewording to "orchestrate, memory/recall, verify return 503 …; triage/ingest fall back to offline mocks".
- O3: README.md:86 parenthetical lists 3 MCP tools while mcp_server.py:191-195 registers 5; the full list of 5 is correctly given at README.md:109-110. Suggest expanding the L86 parenthetical.
