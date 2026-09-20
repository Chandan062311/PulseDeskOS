#!/usr/bin/env bash
# PulseDesk OS smoke checks. Assumes API on localhost:8000, UI on :5173 (dev server).
# UI check is warn-only: a down UI prints WARN but does not fail the run.
set -euo pipefail

API="${API_BASE:-http://localhost:8000}"
UI="${UI_BASE:-http://localhost:5173}"
FAIL=0

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }
warn() { echo "WARN: $1 (continuing)"; }

code_of() { # code_of <url> [curl args...] -> prints HTTP status code
  local url="$1"; shift
  curl -s -o /dev/null -w "%{http_code}" "$@" "$url"
}

# 1. API liveness
code="$(code_of "$API/healthz")"
if [ "$code" = "200" ]; then pass "GET /healthz -> 200"; else fail "GET /healthz -> $code (want 200)"; fi

# 2. Offline triage must return 200 and include an `action` field
triage_body="$(curl -s -w '\n%{http_code}' -X POST "$API/v1/triage" \
  -H 'Content-Type: application/json' \
  -d '{"ticket":{"subject":"VPN down","message":"Cannot reach the VPN since this morning"},"customer":{"plan":"enterprise"}}')"
triage_code="$(printf '%s' "$triage_body" | tail -n1)"
triage_json="$(printf '%s' "$triage_body" | head -n -1)"
if [ "$triage_code" = "200" ] && printf '%s' "$triage_json" | grep -q '"action"'; then
  pass "POST /v1/triage (offline) -> 200 with action field"
else
  fail "POST /v1/triage -> code=$triage_code body=$triage_json (want 200 + action)"
fi

# 3. Memory store then count
store_body="$(curl -s -w '\n%{http_code}' -X POST "$API/v1/memory/store" \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"smoke","text":"smoke probe doc","type":"doc"}')"
store_code="$(printf '%s' "$store_body" | tail -n1)"
store_json="$(printf '%s' "$store_body" | head -n -1)"
if [ "$store_code" = "200" ] && printf '%s' "$store_json" | grep -q '"id"'; then
  pass "POST /v1/memory/store -> 200 with id"
else
  fail "POST /v1/memory/store -> code=$store_code body=$store_json (want 200 + id)"
fi

count_body="$(curl -s "$API/v1/memory/count?tenant_id=smoke")"
if printf '%s' "$count_body" | grep -Eq '"count"[[:space:]]*:[[:space:]]*[1-9][0-9]*'; then
  pass "GET /v1/memory/count?tenant_id=smoke -> $count_body"
else
  fail "GET /v1/memory/count -> $count_body (want count >= 1)"
fi

# 4. Frontend (warn-only)
ui_code="$(code_of "$UI" --max-time 5 || true)"
if [ "$ui_code" = "200" ]; then
  pass "GET $UI -> 200"
else
  warn "GET $UI -> $ui_code (want 200; start UI with 'make ui')"
fi

if [ "$FAIL" -ne 0 ]; then echo "SMOKE: FAIL"; else echo "SMOKE: PASS"; fi
exit "$FAIL"
