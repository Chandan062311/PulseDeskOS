# PulseDesk OS — Stitch prompts

Design system for all three screens: LIGHT mode, Inter headline + Inter body,
ROUND_EIGHT corners, seed color #2563EB, TONAL_SPOT variant. deviceType:
DESKTOP.

Note: Stitch MCP key is in `/home/asus/Typesafe/.mcp.json`. Verify via
ListProjects before calling GenerateScreenFromText.

---

## Screen 1 — Inbox dashboard

Copy-paste into GenerateScreenFromText:

```
PulseDesk OS inbox dashboard, desktop, light mode, Inter font, 8px rounded
corners, primary blue #2563EB tonal-spot theme. Top bar with PulseDesk OS
wordmark, tenant selector, and API status dot. Left sidebar with route
filters (it_access, bug_report, billing, hr_policy, other) and action
filters (auto_route, human_review, quarantine_spam). Main table of support
tickets with columns: subject, sender, route badge, route_confidence bar,
spam_risk indicator, urgency/frustration dots, action chip. Right-side
summary cards: triage volume today, % auto-routed, % human review, spam
quarantined. Clean enterprise SaaS density, no gradients.
```

## Screen 2 — Triage detail with probability bars + memory evidence

Copy-paste into GenerateScreenFromText:

```
PulseDesk OS triage detail view, desktop, light mode, Inter font, 8px
rounded corners, primary blue #2563EB tonal-spot theme. Header with ticket
subject, sender name and email, and TriageResult action chip
(auto_route / human_review / quarantine_spam). Probability bars section for
route_confidence, spam_risk, urgency, frustration, needs_memory,
refund_requested, each labeled 0-1 with numeric value. Reason text block
below the bars. Memory evidence panel listing MemoryHit cards with type
badge (ticket/doc/decision), relevance score, and contradict/injection/PII
flags. Handler result panel with summary and next step. Verify verdict chip
(supported / needs_review / unsupported) with confidence. Enterprise,
readable, dense but calm.
```

## Screen 3 — Review queue

Copy-paste into GenerateScreenFromText:

```
PulseDesk OS human review queue, desktop, light mode, Inter font, 8px
rounded corners, primary blue #2563EB tonal-spot theme. Queue list of
tickets gated to human_review with reason (low route confidence, uncertain
spam band 0.40-0.60 exclusive, route other always reviews). Each row shows subject,
expected route, route_confidence, and gate reason. Detail pane with approve
route, reassign route dropdown (it_access, bug_report, billing, hr_policy,
other), and quarantine spam button. Confidence threshold explainer strip
referencing config.yaml values (0.75 topic, other-always-review).
Audit note field and resolve button. Enterprise operations console style.
```
