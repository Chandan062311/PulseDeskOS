# Auditor C — Release artifacts + docs-truth re-audit (v2-release)

Scope: `RELEASE_v1.md` + `CHANGELOG.md` factual claims vs code; README API table vs
`backend/main.py`; README production section; `ARCHITECTURE.md` gates; `skills/*/SKILL.md`
thresholds; evals goldens vs test assertion; frontend build; scripts; Docker; git tree;
live probes `curl :5173` and `:8000/docs`.
Method: read-only on source (only write is this file). Verified with `rg`/reads,
`bash -n`, `curl`, one `npm run build` (output `dist/` is gitignored → tree unaffected),
one `pytest` run via `/tmp/opencode/pdvenv` (caches pre-existed).

## 1. Claim checks: RELEASE_v1.md + CHANGELOG.md vs code (24 claims)

| # | Claim (doc) | Evidence (code) | Verdict |
|---|---|---|---|
| C1 | RELEASE: 5 endpoint rows — `GET /healthz`, `POST /v1/triage`, `/v1/ingest`, `/v1/orchestrate`, `/v1/verify` | `backend/main.py:190,200,214,277,285` — all 5 decorators present | PASS |
| C2 | RELEASE: 6 memory routes incl. `DELETE /v1/memory/{mem_id}`, `GET .../count` | `backend/main.py:229,238,244,255,261,271` — all 6 present | PASS |
| C3 | RELEASE: Req1 asks 9 questions; `reason` field (not `rationale`) | `backend/triage.py:216-226` returns exactly 9 keys (`route, needs_memory, requests_credentials, sender_identity_mismatch, unexpected_reward, refund_requested, pii_detected, urgency, frustration`); `backend/schemas.py:88` `reason: str` | PASS |
| C4 | RELEASE: `action ∈ {auto_route, human_review, quarantine_spam}` from `config.yaml`, fallbacks only in code | `backend/schemas.py:68-73`; `backend/triage.py:33-41` `_DEFAULT_*` + `_threshold()` readers at `:328-333` | PASS |
| C5 | RELEASE: all 5 routes are classes in single module `backend/handlers/builtins.py`, registered via `register()` | `backend/handlers/builtins.py:211-215` five `register()` calls; `name = it_access/bug_report/billing/hr_policy/other` at `:35,:70,:105,:144,:179` | PASS (but see S2: `handlers/__init__.py` cited in the same sentence is empty) |
| C6 | RELEASE: handlers deterministic, no Jev, only `load_config()` for `handlers.*` | `backend/handlers/builtins.py:13,18-29` — only `load_config` import; no `typesafe_sdk` import; thresholds `sev1_urgency`/`refund_note` at `:93,:130` | PASS |
| C7 | RELEASE: live-only routes 503 without key via `RuntimeError`→503; triage/ingest fall back to offline mock even with `?live=true` | `backend/main.py:131-135` handler; `raise RuntimeError` at `:249,:250,:281,:295`; `_triage_request` at `:185-187` (`if live and key → live else offline`) | PASS |
| C8 | RELEASE: every response carries `X-Request-Id` | `backend/main.py:97-108` middleware; live probe `curl /healthz` returned `x-request-id: 0f920700` | PASS |
| C9 | RELEASE: `POST /v1/memory/store` 422 on empty text; `type` is `Literal["ticket","doc","decision"]` | `backend/main.py:232-233`; `backend/main.py:70`, `backend/schemas.py:96` | PASS |
| C10 | RELEASE: `POST /v1/memory/seed` idempotent; `GET .../list` newest-first; tenant-scoped delete | `backend/orchestrator.py:210-211` (0 when rows exist); `backend/memory_backends/sqlite.py:89` (`ORDER BY rowid DESC`); `:106-113` (`AND tenant_id = ?`, mismatch → False) | PASS |
| C11 | RELEASE: Req2 `bm25_top_k: 30`; auto_capture `true`; `build_memory_questions` in `backend/memory.py` | `config.yaml:24,30`; `backend/memory.py:61`, `:155`; `_auto_capture_enabled` `backend/main.py:144-150` + capture at `:302-308` | PASS |
| C12 | RELEASE: SQLite threading fix (`check_same_thread=False` + lock) + WAL | `backend/memory_backends/sqlite.py:31-34` | PASS |
| C13 | RELEASE: MCP `limit < 1` → `ValueError`; `_req_str` guards on all 5 tools | `backend/mcp_server.py:168-169`; `_req_str` used in all 5 tools (`:93-95,:121-122,:150-152,:167,:180-181`) | PASS |
| C14 | RELEASE: plugin manifest `pulsedesk v0.3.0`; 3 skills + reviewer agent paths | `.claude-plugin/plugin.json:2,4`; `skills/triage|orchestrate|memory/SKILL.md`, `agents/reviewer.md` all exist | PASS |
| C15 | RELEASE: MCP 5 tools `triage_ticket, recall_memory, add_memory, list_memories, verify_response`; same schemas, no duplicate pydantic types | `backend/mcp_server.py:191-195`; imports `Ticket, MemoryHit, VerifyResult` from `.schemas` at `:26`, zero local `BaseModel` subclasses | PASS |
| C16 | RELEASE: evals 14 tickets — billing 4, other 4, it_access 2, bug_report 2, hr_policy 2; auto_route 10, quarantine 2, human_review 2 | Counted `evals/golden-tickets.json`: total 14; routes exactly 4/4/2/2/2; actions exactly 10/2/2 | PASS |
| C17 | RELEASE gates table: spam `>= 0.60`, weights 0.45/0.30/0.25, topic `< 0.75`, uncertain band 0.40–0.60 exclusive, `other` always reviews | `config.yaml:9,12,16-21`; `backend/triage.py:322-326` (weighted sum), `:341` (`>=` quarantine), `:344` (`uncertain_low < spam < uncertain_high`, strict), `:357-363` (`other_always_review`) | PASS |
| C18 | RELEASE gates table: `needs_memory >= 0.60` from `orchestration.*` (not `memory:`); keep 0.70 / drop-injection 0.30 / contradict-flag 0.60; `max_memory_hits: 5`; verify `0.5` | `config.yaml:55-56,25-27,43`; `backend/orchestrator.py:59-60`; `backend/memory.py:52-54,126`; `backend/verify.py:31` | PASS (value-level; behavior caveat S4) |
| C19 | CHANGELOG: dead keys `destructive_confidence_threshold`, `uncertain_floor` removed; `handlers.*`/`verify.*` wired | `rg` over `backend/`, `config.yaml`: zero hits outside CHANGELOG/ARCHITECTURE-history/sandbox notes; `builtins.py:93,130` + `verify.py:31` read the new sections | PASS |
| C20 | CHANGELOG: `recall?live=false` split 503 messages (live-only vs missing-key) | `backend/main.py:248` vs `:250` — two distinct messages | PASS |
| C21 | CHANGELOG: `+2 hr_policy` goldens (14 total); composer plan + open-orders inputs | goldens contain `hr-parental-leave`, `hr-payroll-schedule`; `backend/schemas.py:63-64` (`plan`, `open_orders`), consumed in `triage.py:77-80` | PASS |
| C22 | RELEASE: UI sidebar (Triage/Pipeline/Review/System); 3 stitch prompts; Stitch OAuth-blocked note | `frontend/src/App.tsx:9-12`; `frontend/stitch-prompts.md` Screens 1–3; blocked-note in `frontend/README.md:59-60` + `RELEASE_v1.md:86-89` | PASS |
| C23 | RELEASE "Try it": `docker run -p 8000:8000 --env-file .env -v pddata:/data`; `fastmcp run backend/mcp_server.py`; `sandbox/run_demo.py` | `docker-compose.yml:9,12-13` (MEMORY_DB/volume/ports match); `mcp_server.py:198-199` runnable; `sandbox/run_demo.py` exists | PASS (CWD mixing in snippet noted, cosmetic) |
| C24 | Report-sourced verification block (5/5, 0 crashes, 40 pytest, ruff/mypy clean, validate ✔, 14/14, exit 0, UI 200, API ok) quoted as per-report | `sandbox/report.md:13` (5/5); `sandbox/brutal/REPORT.md:3` (0 crashes), `:45-47` (40 pytest, ruff/mypy, validate, 14/14, exit 0/UI 200/API ok) — quotes are faithful | PASS-as-quotation (current-state drift: S5, S6) |

## 2. README API table vs `backend/main.py` routes

README table (11 rows, `README.md:43-53`) vs 11 decorators (`main.py:190,200,214,229,238,244,255,261,271,277,285`):
all 11 documented, all 11 real — **no undocumented route, no phantom row**. Minor nits (not verdict-driving):
`DELETE /v1/memory/{id}` vs code `{mem_id}` (param name only); `Output` column types check out
(`IngestResponse` is defined in `main.py:58`, `OrchestrateResponse` in `schemas.py:120`).
**However:** `README.md:38-39` "All contracts are frozen Pydantic models in `backend/schemas.py`" is
false — `TriageRequest, IngestResponse, MemoryStoreRequest, MemoryRecallRequest, VerifyRequest,
OrchestrateRequest` all live in `backend/main.py:51-94` (see S3).

## 3. README production section accuracy (`README.md:61-78`)

| Item | Check | Result |
|---|---|---|
| `docker compose up --build -d # api :8000 (4 workers, WAL sqlite) + ui :8080` | `docker-compose.yml:10` `--workers 4`; `:14` `8000:8000`; `:26` `8080:80`; `sqlite.py:34` WAL | PASS |
| `./scripts/smoke.sh`, `./scripts/backup.sh ./backups` | Both exist, `bash -n` clean, `backup.sh` uses online `sqlite3.backup()` + `MEMORY_DB` | PASS |
| `docker build -t pulsedesk-os:1.0 . # verified 216MB`; `pulsedesk-ui:1.0 ./frontend # verified 63MB` | `docker images`: `pulsedesk-os:1.0 216MB`, `pulsedesk-ui:1.0 63.1MB` — exact | PASS |
| `/healthz` open, everything else needs `X-API-Key` (`README.md:64-65`) | `main.py:111-128` gates all but `/healthz`; `/docs` → 401 on keyed server confirms | PASS (by design; see P2) |
| CI runs ruff + mypy strict + pytest + Vite build | `.github/workflows/ci.yml` — all four present | PASS |
| **Live-Jev 503 sentence (`README.md:55-56`): "(orchestrate, memory/recall, verify, triage?live=true) return 503 … when `TYPESAFE_API_KEY` is missing"** | **Code `_triage_request` (`main.py:185-187`): `?live=true` without key falls back to offline mock, never 503** | **FAIL (S1)** |

Makefile targets (`setup, api, ui, test, smoke, build-ui`) all exist; `smoke`→`scripts/smoke.sh`,
`build-ui`→`npm run build` correctly wired.

## 4. ARCHITECTURE gates vs code — PASS on values/edges, 2 prose drifts

Quarantine/human-review/auto-route semantics (`ARCHITECTURE.md:58-73`) match `triage.py:341-363`
including exclusive band edges and `other_always_review`; dead-key removal note (`:76-78`) matches
code (C19). Drifts: (a) `ARCHITECTURE.md:30` + `README.md:150` "one file per route" vs the single
`backend/handlers/builtins.py` (S2); (b) "flagging `contradicts >= 0.60` before the handler drafts"
(`ARCHITECTURE.md:70-73`, echoed `RELEASE_v1.md:108`) — `compose_recall` binds `_flag` but never
uses it (`memory.py:117`), and neither `orchestrator.py` nor MCP filters/flags on contradicts; the
score is carried on `MemoryHit` only (S4).

## 5. `skills/*/SKILL.md` thresholds vs `config.yaml` — all PASS

triage SKILL (`0.60 / 0.40–0.60 exclusive / 0.75 / other`, `:19-22`) = `config.yaml:9,12,19-21` + code.
orchestrate SKILL (`needs_memory >= 0.60`, `contradicts >= 0.60`, `injection >= 0.30`, `:18-20`) =
config + reviewer agent (`agents/reviewer.md:15-16`) consistent. memory SKILL (`0.70/0.30/0.60`,
`top_k = 30`, skill-suggest `0.30/0.30/3`, `:32-34`) = `config.yaml:24-26,32-36`. Note: `skill_suggest.*`
is documented only for the SKILL recipe — never imported by code (already flagged in
`sandbox/brutal/contracts.md:91,101`; not claimed otherwise by release docs).

## 6. Evals goldens vs test assertion — PASS (with stale docstring)

`tests/test_triage.py:242` asserts `len(raw) == 14` → matches file (14). But the docstring on `:239`
says "has **12** well-formed tickets" (S7), and the route-subset assertion on `:243` omits `hr_policy`.

## 7. Build / scripts / Docker / git / probes

- Frontend build: `npm run build` → success (`33 modules`, `dist/` emitted). PASS.
- `scripts/smoke.sh`, `scripts/backup.sh`: `bash -n` clean. PASS. (`backup.sh:5` default
  `pulsedesk-os/memory.db` is CWD-relative; works via `MEMORY_DB` in compose/prod, cosmetic.)
- `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`: present; compose services (`api`, `ui`)
  match Dockerfiles; `pddata` volume wired. PASS.
- `git log`: 2 commits (`4507440`, `81d044b`). `git status --short` at audit time: **one untracked
  entry `?? sandbox/brutal/v2-auth.md`** — a sibling auditor's in-progress output, not a release
  artifact; `.env`/`memory.db`/`dist/` correctly untracked-via-`.gitignore` and **no secrets in
  `git ls-files`** (only `.env.example` tracked). See S8.
- Probes: `curl :5173` → **200** (P1 PASS). `curl :8000/docs` → **401** — expected on the keyed
  server: the auth middleware (`main.py:111-128`) exempts only `/healthz`, which is exactly what
  `README.md:64-65` documents (P2, by design, not a bug).

## 8. SHORTCOMINGS (file:line evidence)

- **S1 (verdict-driving, false claim in release docs).** `README.md:55-56` states `triage?live=true`
  returns 503 without a key. Code (`backend/main.py:185-187`) falls back to the offline midpoint mock;
  `RELEASE_v1.md:34-38` states the correct behavior, so the two frozen docs contradict each other.
  Fix: drop `triage?live=true` from the README 503 list.
- **S2 (verdict-driving, false file-path claim).** `README.md:150` ("one file per route (it_access,
  bug_report, …)"), `README.md:142-143` ("Add a handler = new file under `backend/handlers/`"),
  `ARCHITECTURE.md:30` ("One file per `Route`") vs reality: single module
  `backend/handlers/builtins.py` (all 5 classes + 5 `register()` calls, `:211-215`) and an **empty**
  `backend/handlers/__init__.py`. `RELEASE_v1.md:28-31` describes this correctly; README/ARCHITECTURE
  do not. Related: `RELEASE_v1.md:31` cites `handlers/__init__.py` as part of the registry path —
  harmless but misleading given the file is empty.
- **S3 (false claim).** `README.md:38-39` "All contracts are frozen Pydantic models in
  `backend/schemas.py`" vs `TriageRequest, IngestResponse, MemoryStoreRequest, MemoryRecallRequest,
  VerifyRequest, OrchestrateRequest` defined in `backend/main.py:51-94`.
- **S4 (overstated behavior).** "Flagging `contradicts >= 0.60`" (`ARCHITECTURE.md:70-73`,
  `RELEASE_v1.md:108`): threshold default exists (`memory.py:54`), but `_flag` is discarded at
  `memory.py:117` and no caller acts on it.
- **S5 (stale quality-gate claim).** Release (via `REPORT.md:45`) claims "`mypy` (strict) clean";
  current `mypy backend` (strict, `pyproject.toml:31-36`) reports 2 errors:
  `backend/jev_client.py:8`, `backend/main.py:127` (unused `type: ignore`, mypy 2.3.1). `ruff` passes.
- **S6 (count drift, report-sourced).** Release (via `REPORT.md:45`) claims "40 pytest passed";
  suite now collects and passes **53** (`pytest -q`: 53 passed). Quote is faithful to the report;
  the report is stale relative to the tree.
- **S7 (stale test docstring).** `tests/test_triage.py:239` "has 12 well-formed tickets" vs asserted
  and actual 14; `:243` route-subset check omits `hr_policy`.
- **S8 (tree hygiene at audit time).** `git status --short` → `?? sandbox/brutal/v2-auth.md`
  (concurrent auditor output, not mine — this audit wrote only this file). Secrets check passes:
  `.env` untracked and gitignored (`.gitignore:5`), `git ls-files` contains no secret material.
- Minor (non-verdict): `backend/orchestrator.py:9` "8 parallel judgments" vs 9 questions
  (`triage.py:216-226`); `ARCHITECTURE.md:7` flow box lists `reason` among "9Qs" while omitting the
  three spam sub-questions; `frontend/README.md:30` hardcodes a session-local venv path.

## Verdict: FAIL

False claims in frozen release docs (S1: README 503 sentence contradicts `main.py:185-187`;
S2: "one file per route" contradicts single-module `builtins.py`; S3: "all contracts in schemas.py"
contradicts `main.py:51-94`). No undocumented routes (11/11 both directions), no broken script
references (`bash -n` clean, both wired into Makefile/CI), image size claims verified byte-for-byte
(216MB / 63.1MB). Tree has one untracked file from parallel audit activity (S8); no secrets tracked.

## Final message

Checked **24 release/changelog claims: 23 PASS** (C24 as faithful quotation), **1 FAIL-relevant
README sentence (S1)** plus **2 more false README/ARCHITECTURE statements (S2, S3)**. All 11 API
routes documented and real; all gate values/edges match code and `config.yaml`; MCP tools (5),
goldens (14, exact route/action split), skills thresholds, Docker sizes (216MB/63.1MB exact),
`bash -n`, `ruff`, and `npm run build` all PASS. Top findings: (1) README's `triage?live=true`→503
claim is false — code falls back to the offline mock (`main.py:185-187`), contradicting
`RELEASE_v1.md:34-38`; (2) "one file per route" is false — all handlers live in `builtins.py` with
an empty `__init__.py`; (3) request/response models live in `main.py`, not only `schemas.py`;
(4) current `mypy --strict` shows 2 unused-ignore errors and pytest now passes 53 (not the
report's 40) — report-sourced claims gone stale; (5) live probes `:5173`→200, `:8000/docs`→401
(auth-gated by design). **Verdict: FAIL** (false claims in release docs).
