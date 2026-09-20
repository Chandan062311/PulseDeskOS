# PulseDesk OS re-audit — Auditor A (auth + security) — v2

Date: 2026-09-20 · API: `http://localhost:8000` (`PULSEDESK_API_KEY=dev-key`, header `X-API-Key: dev-key`) · Python: `/tmp/opencode/pdvenv/bin/python` · Repo: `/home/asus/Typesafe/pulsedesk-os`
Source was READ-ONLY; this file is the only write.

## VERDICT: PASS

No FAIL condition met: every `/v1/*` route returns 401 without/wrong key, zero 500s anywhere, key via query param rejected, no secret material in tracked files.

## Probe table

| # | Probe | Result |
|---|-------|--------|
| 1 | `GET /healthz` without key | 200 `{"status":"ok"}` — open liveness, as designed |
| 2 | All 10 `/v1/*` routes without key (`POST /v1/triage`, `POST /v1/ingest`, `POST /v1/memory/store`, `POST /v1/memory/seed`, `POST /v1/memory/recall`, `GET /v1/memory/list`, `DELETE /v1/memory/nonexistent`, `GET /v1/memory/count`, `POST /v1/verify`, `POST /v1/orchestrate`) | 10/10 → **401** `{"detail":"Invalid or missing API key."}` |
| 3 | All 10 `/v1/*` routes with wrong key (`wrong-key`) | 10/10 → **401** |
| 4 | Empty `X-API-Key:` header (triage, memory/list, orchestrate) | **401** |
| 5 | Key via query param (`?api_key=dev-key`, `?x-api-key=dev-key` on triage + memory/list) | **401** — header only, not accepted via query |
| 6 | `HEAD`/`OPTIONS` on protected routes without key | **401** (middleware gates before routing; `/healthz` HEAD/OPTIONS → 405, open but method-rejected) |
| 7 | `HEAD`/`OPTIONS` on GET routes with key | **405**, no 500 |
| 8 | `/docs`, `/openapi.json`, `/redoc` without key | **401** (schema hidden from unauthenticated); with key → **200** |
| 9 | 20 parallel gated `GET /v1/memory/count` with key | 20/20 → **200** |
| 10 | 20 parallel mixed (10 good / 10 bad keys) | 10× **200** + 10× **401**, zero 500s |
| 11 | Rate limit: 100 rapid sequential gated requests | 100× **200** in ~0.3s — **no rate limiting observed** (see S2) |
| 12 | Unknown route `GET /v1/nonexistent`: no key → **401** (fail-closed ordering), with key → **404**; trailing-slash `/v1/memory/list/` no key → **401**, with key → **200** |
| 13 | `git check-ignore .env` → ignored via `.gitignore:5`; `git ls-files` tracks only `.env.example` (placeholders `your-key-here` / `change-me-in-production`), no live key material in tracked files (`git grep` for `apikey_`/`sk-`/`Bearer` hits are placeholders, doc variable refs, and prior-audit pattern mentions only) |
| 14 | `docker-compose.yml`: `env_file: .env`, `environment:` carries only `MEMORY_DB` — **no hardcoded secret**; `Dockerfile` contains no secret refs |

Counts: 10/10 routes gated without key · 10/10 rejected with wrong key · 0× 500 across all probes (incl. mixed parallel, bad methods, unknown routes, NUL-byte key → 400) · 0 unprotected `/v1` routes · 0 query-param acceptances · 0 secrets in tracked files.

## SHORTCOMINGS (with repros)

- **S1 (low) — non-constant-time key compare, `backend/main.py:126`.** `request.headers.get("x-api-key","") != expected` instead of `hmac.compare_digest`. Repro: code inspection. Timing note only (per brief, not exploited): mean good-key latency ~2.7ms vs bad-key ~1.5ms over 30 samples — delta is dominated by downstream handler work after the gate, not the compare itself; not remotely exploitable, but switch to `compare_digest` on principle.
- **S2 (medium) — no rate limiting.** Repro: `/tmp/opencode/pdvenv/bin/python -` loop of 100× `GET /v1/memory/count` with key → `Counter({200: 100})` in ~0.3s, no 429; 20-way parallel all 200. Brute-force/DoS posture relies entirely on key secrecy + infra. Consider a limiter (e.g. slowapi) or document that a reverse proxy must enforce it.
- **S3 (medium) — auth silently disabled when `PULSEDESK_API_KEY` is unset (`backend/main.py:123-125`).** Documented local-dev behavior, but fail-open: a prod deploy with a missing/empty `.env` (which is gitignored, so never shipped) serves all `/v1/*` unauthenticated with only a code comment as guard. Repro: code inspection. Recommend fail-closed when `ENV`/prod flag is set, or at least a loud startup warning.
- **S4 (low) — `.env` permissions `644` (`-rw-rw-r--`, 242 bytes, contents not read).** Group/world-readable on shared hosts. Recommend `chmod 600 .env`.
- **S5 (info, not a bug) — HTTP OWS trimming around the key.** `" dev-key "` (surrounding spaces) → 200, `"dev -key"` (internal space) → 401, `"DEV-KEY"` → 401, NUL byte → 400 (no 500). Repro: `urllib.request.Request(..., headers={"X-API-Key":" dev-key "})`. Leading/trailing whitespace is stripped at the HTTP layer per RFC 9110; comparison itself is strict. No action needed; recorded for completeness.
