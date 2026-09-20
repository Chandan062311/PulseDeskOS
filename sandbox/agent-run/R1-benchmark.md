# R1 Benchmark — Live Pipeline Latency (scout, read-only)

Routed by Jev: worker=scout conf=1.00. All numbers below were measured live against
http://localhost:8000 on 2026-09-20. No files were modified except this findings file.

## Results

| endpoint | n | p50 | max |
|---|---|---|---|
| POST /v1/triage?live=true | 10 | 1.127 s | 1.252 s |
| POST /v1/memory/recall | 10 | 0.0009 s | 0.0014 s |
| POST /v1/orchestrate | 5 | 3.371 s | 3.605 s |

## Raw samples (seconds, wall-clock per request, all HTTP 200)

- triage (n=10): 1.252, 1.217, 1.063, 1.148, 1.088, 1.206, 1.116, 1.138, 1.116, 1.085
- recall (n=10): 0.0014, 0.0012, 0.0010, 0.0009, 0.0008, 0.0008, 0.0009, 0.0009, 0.0009, 0.0010
- orchestrate (n=5): 3.605, 3.349, 3.561, 3.369, 3.371

## Method note

- Client timing via `time.perf_counter()` around each HTTP POST (urllib, `/tmp/opencode/pdvenv/bin/python`, Python 3.12.3), sequential samples, timeout 120 s.
- p50 = median (average of two middle values for even n); max = slowest sample.
- Triage body: `{"ticket":{"subject":"Latency probe","message":"VPN not working, need access before Monday","sender":{"display_name":"T","email":"t@acme.com"},"links":[]}}` with `?live=true`.
- Recall body: `{"tenant_id":"bench","query":"refund policy duplicate charge"}`. No seeding was needed: `GET /v1/memory/count` returned `{"count":3}` and `POST /v1/memory/seed` returned `{"seeded":0}` (store already populated).
- Orchestrate body: same triage ticket + `"tenant_id":"bench"` (5 samples; slower because it runs the full triage → recall → dispatch → verify pipeline with live Jev).
- Server health during run: `GET /healthz` → `{"status":"ok"}`.
- Nothing uncertain: every request returned HTTP 200 and every latency above was directly observed.
