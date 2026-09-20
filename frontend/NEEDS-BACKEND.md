# PulseDesk OS — Backend Gap Specification (NEEDS-BACKEND.md)

This document tracks backend endpoints and data shapes required by the Stitch UI screens that are not currently exposed by `backend/main.py`.

---

## 1. Persistent Ticket Stream & Inbox (`GET /v1/tickets`)

- **Screen**: Screen 1 — Operations Console / Inbox Dashboard (`inbox.html`)
- **Requirement**: An endpoint to retrieve a paginated stream of inbound support tickets.
- **Proposed Signature**:
  ```http
  GET /v1/tickets?route={route}&action={action}&search={q}&limit=50&offset=0
  ```
- **Response Shape**:
  ```json
  {
    "items": [
      {
        "id": "PD-8924",
        "subject": "Duplicate charge",
        "sender": "user@acme.com",
        "message": "...",
        "plan": "enterprise",
        "open_orders": ["A-104"],
        "triage": {
          "route": "billing",
          "route_confidence": 0.94,
          "spam_risk": 0.02,
          "urgency": 0.78,
          "frustration": 0.65,
          "action": "auto_route",
          "reason": "..."
        },
        "created_at": "2026-09-20T14:02:18Z"
      }
    ],
    "total": 1248
  }
  ```
- **Current UI Behavior**: Front-end renders high-density sample tickets (`INITIAL_INBOX_TICKETS`), with an "Inspect" button that feeds the live triage engine.

---

## 2. Real-Time Triage Metrics (`GET /v1/metrics/triage-summary`)

- **Screen**: Screen 1 — KPI Metrics Rail
- **Requirement**: Aggregated counters for operational dashboard metrics.
- **Proposed Signature**:
  ```http
  GET /v1/metrics/triage-summary?timeframe=today
  ```
- **Response Shape**:
  ```json
  {
    "total_volume": 4892,
    "auto_routed_count": 3512,
    "auto_routed_pct": 71.8,
    "human_review_count": 1106,
    "human_review_pct": 22.6,
    "quarantined_spam_count": 274,
    "quarantined_spam_pct": 5.6
  }
  ```
- **Current UI Behavior**: Computed locally from loaded ticket set.

---

## 3. Server-Side Persistent Review Queue (`GET /v1/review-queue`)

- **Screen**: Screen 3 — Human Review Queue (`review-queue.html`)
- **Requirement**: Endpoint to query tickets currently gated to `human_review` (due to low route confidence `< 0.75`, spam band `0.40–0.60`, or fallback route `other`).
- **Proposed Signature**:
  ```http
  GET /v1/review-queue?filter={all|low_confidence|borderline_spam|other}
  ```
- **Response Shape**:
  ```json
  {
    "items": [
      {
        "ticket_id": "PD-8932",
        "subject": "Something seems off",
        "sender": "user@acme.com",
        "message": "...",
        "predicted_route": "other",
        "route_confidence": 0.48,
        "spam_risk": 0.45,
        "gate_reason": "Route other always requires review",
        "created_at": "2026-09-20T14:10:00Z"
      }
    ],
    "total": 3
  }
  ```
- **Current UI Behavior**: Populated by session triage results where `action !== 'auto_route'`, merged with sample review exceptions.

---

## 4. Review Queue Audit & Resolution (`POST /v1/review/{ticket_id}/resolve`)

- **Screen**: Screen 3 — Ticket Resolution & Dispatch Panel
- **Requirement**: Immutable logging of operator overrides, audit notes, and dispatch actions.
- **Proposed Signature**:
  ```http
  POST /v1/review/{ticket_id}/resolve
  Content-Type: application/json

  {
    "action": "approve" | "reassign" | "quarantine_spam",
    "override_route": "billing",
    "audit_note": "Verified duplicate capture against Stripe ledger.",
    "operator_id": "op_current"
  }
  ```
- **Current UI Behavior**: Logs resolution action to client-side state and displays confirmation toast.

