---
description: Triage a support ticket with TypeSafe Jev — route, spam risk, urgency, gated action. Use when a ticket, email, or chat message needs classification and routing.
---

# PulseDesk triage

Routed via the plugin MCP server (`mcp__plugin_pulsedesk_pulsedesk__triage_ticket`)
or the backend API (`POST /v1/triage?live=true`).

## Inputs ($ARGUMENTS)

`$ARGUMENTS` is the ticket text. If empty, ask for subject, message, and sender email.

## Procedure

1. Call `triage_ticket(subject, message, sender_email)`.
2. Read the gated result — do not second-guess the gates in prose.
   Routes: `it_access | bug_report | billing | hr_policy | other`.
   - `quarantine_spam` when `spam_risk >= 0.60`
   - `human_review` when spam is strictly between 0.40 and 0.60
     (edges fall through), `route_confidence < 0.75`,
     or route is `other` (no owning team)
   - else `auto_route`
   Also surface `pii_detected`: when high, warn that the ticket holds
   sensitive data before quoting it anywhere.
3. Report: route + confidence bar, spam risk, urgency, action, and the `reason`
   string verbatim. For `human_review`/`quarantine_spam`, say what a human must
   check next instead of acting.
