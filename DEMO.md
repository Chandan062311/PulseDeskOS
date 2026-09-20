# Live demo script — PulseDesk OS (5 minutes)

Audience: anyone who has suffered a support queue. One link, three acts.
No slides needed; the numbers are the slides.

## Setup (before the audience arrives)

1. Backend live with key (`/v1/status` → `jev: live`), UI open on Inbox.
2. Safety net: if venue Wi-Fi dies, triage still runs in offline mock mode —
   say so out loud, it demos the degradation design instead of failing.

## Act 1 — The outage (60s): speed

> "Checkout is down. Watch what happens with zero humans involved."

Inbox → Inspect the API-500s ticket → **Triage live**: `bug_report`,
urgency **1.0**, auto-routed. Point at the confidence bar: the system shows
its math instead of hiding it.

## Act 2 — The attack (60s): safety

> "Now someone tries to rob us."

Load the bonus/OTP message → **Triage live**: `quarantine_spam`, spam 0.86.
It never reaches a handler or a customer. Mention the 60+ adversarial cases
in `sandbox/brutal/` with zero crashes.

## Act 3 — The pipeline (2 min): the whole product in one call

Pipeline tab → duplicate-charge ticket → **Run orchestration**. Narrate the
four stages as they land: triage → memory hit cited → handler → verify
verdict → decision saved back as memory. End on the draft reply: every claim
traces to evidence.

## Closer (30s)

> "Code owns the workflow, Jev supplies the judgments — 9 questions,
> ~1 second, every number shown. Star it, clone it, `make setup` and break it:
> `sandbox/brutal/` tells you exactly how we tried."

## If asked…

- *"Why not an LLM agent?"* — agents choose their own next step every loop;
  here code owns control flow and Jev answers narrow typed questions with
  calibrated probabilities. Faster, cheaper, auditable.
- *"What about our data?"* — tenant-scoped memory, SQLite/Postgres behind a
  protocol, PII flagged, injection-gated recall.
- *"Can I use the pieces?"* — MCP server (5 tools), Claude plugin
  (`/pulsedesk:triage`), or plain REST — all in the README.
