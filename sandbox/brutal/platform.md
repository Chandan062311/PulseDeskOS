# Adversary C — Platform / API / MCP sweep (PulseDesk OS)

- Date (UTC): 2026-09-20. Target: `http://localhost:8000` (already running, `GET /healthz` 200).
- Repo: `/home/asus/Typesafe` (READ-ONLY; no source modified). Python: `/tmp/opencode/pdvenv/bin/python` with `sys.path.insert(0,'pulsedesk-os')`.
- Server env note: `TYPESAFE_API_KEY` **is set** server-side (orchestrate/verify/recall-live all executed live Jev calls). `live=false` paths therefore test the offline/503 branches, not a missing-key deploy.
- FAIL definition used: 500 on bad input, missing request-ids if documented, concurrency errors (500/timeout), MCP crash, or latency >120s. Anything else is PASS with notes; contract smells go to SHORTCOMINGS.

## Findings

| # | Case | Request | Status | Latency | X-Request-Id | Verdict |
|---|------|---------|--------|---------|--------------|---------|
| 1a | Malformed JSON `{bad json` → `/v1/triage` | raw body | 422 `json_invalid` | ~17ms | present (`86a82765`) | PASS |
| 1b | Malformed `{"ticket": {"message": }` | raw body | 422 `json_invalid` | ~1ms | present | PASS |
| 1c | `not json at all` | raw body | 422 `json_invalid` | ~1ms | present | PASS |
| 1d | Empty body | raw, 0 bytes | 422 `missing body` | ~1ms | present | PASS — never 500 |
| 2a | `message` as number (`12345`) | POST `/v1/triage` | 422 `string_type` @ `ticket.message` | ~1–18ms | present | PASS |
| 2b | `sender` as string | POST `/v1/triage` | 422 `model_attributes_type` @ `ticket.sender` | ~1ms | present | PASS |
| 2c | `customer` as string | POST `/v1/triage` | 422 `model_attributes_type` @ `customer` | ~1ms | present | PASS |
| 3a/b/c | Missing `ticket` (`{}`, customer-only, `ticket:null`) | POST `/v1/triage` | 422 (`missing` / `model_attributes_type`) | ~1ms | present | PASS |
| 4a | Extra field inside frozen `Ticket` (`EVIL`) | POST `/v1/triage` | 422 `extra_forbidden` | ~1ms | present | PASS |
| 4b | Extra field inside frozen `Sender` (`extra`) | POST `/v1/triage` | 422 `extra_forbidden` | ~1ms | present | PASS |
| 4c | Extra **top-level** field (`zzz_unknown`) on `TriageRequest` | POST `/v1/triage` | **200 (silently ignored)** | ~1ms | present | PASS (no 500) — but see S1 |
| 4d | Extra top-level on `/v1/verify` | POST | 200, live verify ran (~1.2s) | ~1199ms | present | PASS — see S1 |
| 4e | Extra top-level on `/v1/orchestrate` | POST | 200, pipeline ran | ~2314ms | present | PASS — see S1 |
| 4f | Extra top-level on `/v1/memory/store`, `/v1/memory/recall` | POST | 200 (ignored) | ~4ms / ~1ms | present | PASS — see S1 |
| 5 | GET on POST-only routes (`/v1/triage`, `/v1/ingest`, `/v1/verify`, `/v1/orchestrate`, `/v1/memory/store`, `/v1/memory/recall`, `/v1/memory/seed`) | GET | 405 `Method Not Allowed` ×7 | ~1ms | present on all | PASS |
| 6 | `/v1/orchestrate` `seed=false`, fresh tenant `brutal-fresh` | POST | 200, `memory_hits: []` on first call; triage `it_access/auto_route`, handler `it_access` | ~2045ms | present | PASS — memory empty as expected; see S7 for repeat-call note |
| 7a | `/v1/verify` empty reply + empty evidence | POST | 200 `{"supported":0.0,"confidence":1.0,"verdict":"needs_review"}` | ~1161ms | present | PASS (no 500) |
| 7b | `/v1/verify` reply set, evidence empty | POST | 200 `{"supported":0.01,...,"verdict":"unsupported"}` | ~1156ms | present | PASS |
| 7c/d | `/v1/verify` missing `evidence` / wrong types (`reply:123`) | POST | 422 | ~1ms | present | PASS |
| 8a | `/v1/memory/recall?live=false` | POST | 503 `{"detail":"Memory recall needs live Jev: set TYPESAFE_API_KEY."}` | ~2ms | present | PASS (expected 503 w/ key message; see S8) |
| 8b | `/v1/memory/recall` (default `live=true`, key set) | POST | 200 `[]` | ~1ms | present | PASS |
| 9 | `X-Request-Id` presence | all sampled 200/422/405/503 | present everywhere (lowercase `x-request-id` on wire) | — | present | PASS |
| 10 | Concurrency: 20 parallel `POST /v1/triage?live=false` (threads) | 20× | **20/20 → 200**, 0× 500, 0 timeouts | wall 262ms; min 189 / **p50 ~218** / max 258ms | all present | PASS — see S5 for slowdown note |
| 11 | Concurrency: 5 parallel `POST /v1/orchestrate` (live Jev, tenant `brutal-load`, `seed:false`) | 5× | **5/5 → 200**, 0 errors | wall 2.44s; min 2286 / **p50 2340** / max 2440ms | all present | PASS (far below 120s) |
| 12a | MCP `triage_ticket("", "")`, `("","")`, 5KB message | direct import | OK, offline stub `human_review`, no crash | ~0ms | n/a | PASS |
| 12b | MCP `triage_ticket("s", None)` | direct | raises `pydantic.ValidationError` (`string_type`), no process crash | ~0ms | n/a | PASS — see S4 |
| 12c | MCP `recall_memory` empty + 5KB query | direct | OK (`hits:[]`, `candidates_considered:3`) | ~0–15ms | n/a | PASS |
| 12d | MCP `add_memory` empty + 5KB + bogus `type="weirdtype"` | direct | OK, ids returned, **no type validation** | ~2–3ms | n/a | PASS — see S2 |
| 12e | MCP `list_memories` fresh tenant / `limit=0` / `limit=-1` | direct | OK (fresh tenant auto-seeds 3 demo docs; 0/-1 → `memories:[]`, `count:6`) | ~0–7ms | n/a | PASS — see S3 |
| 12f | MCP `verify_response("", "")` + 5KB/5KB | direct | OK, offline stub `needs_review` | ~0ms | n/a | PASS |
| 13 | `GET /docs` | GET | 200 Swagger UI HTML | ~1ms | present | PASS |
| 14a | `/v1/orchestrate` 8KB message (`seed:false`) | POST | 200 `human_review`/`other`, full pipeline | ~2258ms | present | PASS |
| 14b | `/v1/triage?live=false` 8KB message (contrast) | POST | 200 offline mock | ~2ms | present | PASS |

No 500 observed on any bad input. No timeouts. Slowest call: 5-way orchestrate max 2440ms — 50× under the 120s bar.

## SHORTCOMINGS (numbered + repro)

- **S1. Top-level request wrappers silently ignore unknown fields (nested `Frozen` models 422).** `TriageRequest`, `VerifyRequest`, `OrchestrateRequest`, `MemoryStoreRequest`, `MemoryRecallRequest` in `backend/main.py` are plain `BaseModel` (default `extra='ignore'`), while `Ticket`/`Sender`/etc. in `backend/schemas.py` are `Frozen(extra='forbid')`. A typo'd client field at the top level is silently dropped yet the (billable, ~1–2s live) pipeline still runs.
  - Repro: `POST /v1/triage {"ticket":{"subject":"t","message":"hi"},"zzz_unknown":123}` → 200 (vs `{"ticket":{...,"EVIL":"x"}}` → 422). Same for `POST /v1/verify {"reply":"r","evidence":"e","zzz":1}` → 200 after ~1.2s live call; `POST /v1/orchestrate {...,"zzz":1}` → 200 after ~2.3s.
- **S2. MCP `add_memory` accepts arbitrary `type` strings.** `backend/mcp_server.py::add_memory` passes `type` straight to the backend; `add_memory("brutal-mcp", <5KB>, "weirdtype")` → `{"id": ...}` with no 422, while `MemoryHit.type` is `Literal["ticket","doc","decision"]`. Junk types will poison recall/type filters later.
- **S3. MCP `list_memories` silently coerces `limit=0` / `limit=-1` to empty list.** Returns `{"memories": [], "count": 6}` instead of a validation error — harmless but masks caller bugs.
- **S4. MCP `triage_ticket` with `None` message raises raw `pydantic.ValidationError` to the caller.** No crash (FastMCP surfaces it as a tool error), but unlike the HTTP layer there is no friendly 422-shaped envelope; MCP clients see an unhandled-looking traceback string.
  - Repro: `sys.path.insert(0,'pulsedesk-os'); from backend.mcp_server import triage_ticket; triage_ticket("s", None)` → `ValidationError: ... message: Input should be a valid string`.
- **S5. ~100× triage latency inflation under 20-way concurrency (no errors, but notable).** Sequential `POST /v1/triage?live=false` ≈ 1–2ms; under 20 parallel threads each takes ~190–260ms (p50 ~218ms, wall 262ms). Zero 500s so not a FAIL, but suggests event-loop/executor contention worth profiling before raising concurrency limits.
- **S6. Missing `Content-Type` yields a confusing 422.** `POST /v1/triage` with a valid JSON body but no content-type → 422 `model_attributes_type: "Input should be a valid dictionary..."` with `input` shown as the raw string. Correct status, misleading message — clients will misread it as a schema error rather than "set Content-Type: application/json".
- **S7. `seed=false` "fresh tenant, memory empty" holds only for the first orchestrate call.** Resolved `auto_route` tickets auto-capture decision memories, so my second `brutal-fresh` call returned `memory_hits` non-empty and `GET /v1/memory/count?tenant_id=brutal-fresh` → `{"count": 2}` (likewise `brutal-load` → 5 after the 5-way run). Expected behavior, but test isolation must use a unique tenant per run.
- **S8. Misleading 503 detail on `recall?live=false` when a key IS set.** `POST /v1/memory/recall?live=false` → 503 `"Memory recall needs live Jev: set TYPESAFE_API_KEY."` even though the server demonstrably has a key (live recall/orchestrate/verify all worked). The message doesn't distinguish "caller asked for offline" from "server missing key". Minor.
- **S9 (info). Unknown query params silently ignored.** `POST /v1/orchestrate?live=true` → 200 with no effect (orchestrate has no `live` flag). Consistent with FastAPI defaults; flagging only because case 6 explicitly probed it.
