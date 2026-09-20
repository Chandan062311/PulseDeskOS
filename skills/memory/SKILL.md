---
description: Tenant-scoped memory layer with Jev-reranked recall — store, search, list, delete. Use when the task needs past tickets, policy docs, or decisions as evidence.
---

# PulseDesk memory — tenant-scoped layer with Jev-reranked recall

Backend: plugin MCP server (`mcp__plugin_pulsedesk_pulsedesk__recall_memory`,
persistent SQLite store shared with the API) or HTTP:

- `POST /v1/memory/store` → `{id}` — add a doc/decision for a tenant.
- `POST /v1/memory/recall` → reranked `MemoryHit`s (live Jev).
- `GET /v1/memory/list?tenant_id=&limit=` → newest-first rows.
- `DELETE /v1/memory/{id}` → remove one memory.
- `GET /v1/memory/count?tenant_id=` → tenant size.
- Resolved `auto_route` tickets auto-capture as `decision` memories
  (`memory.auto_capture_resolved` in `config.yaml`).

## Tools (MCP, persistent shared store)

- `recall_memory(tenant_id, query)` → filtered `MemoryHit`s (relevance,
  contradicts, injection, PII already gated).
- `verify_response(reply, evidence)` → `supported` / `needs_review` /
  `unsupported` verdict.
- `add_memory(tenant_id, text)` / `list_memories(tenant_id)` → write and
  browse the same store the API serves.

Offline stubs return mid values and note that live Jev calls need
`TYPESAFE_API_KEY`.

## Thresholds (`config.yaml`)

- Memory: keep `relevance >= 0.70`, drop `injection >= 0.30`,
  flag `contradicts >= 0.60` for human review. BM25 shortlist `top_k = 30`.
- Skill suggest: gate `0.30`, fits `0.30`, shortlist `3`.

## `suggest()` 2-stage recipe

Call 1 — rank + gate: one `Choice` over candidate skills plus one `Noul`
gate per candidate (`should_suggest`, `fits_context`, `is_safe_to_auto_run`).
If `mean(gates) < 0.30`, stay quiet and suggest nothing.

Call 2 — confirm shortlist: one `Choice` over the top-3 shortlist plus one
`fits` `Noul` per skill. Reject any skill with `fits < 0.30`.

```python
from typesafe_sdk import Choice, Noul, TypeSafeClient

with TypeSafeClient() as client:
    call1 = client.system_one(
        state={"request": request_text, "skills": ["refund", "vpn", "billing"]},
        questions={
            "rank": Choice(
                instructions="Which skill best fits the request at `request`?",
                criteria={"refund": None, "vpn": None, "billing": None},
            ),
            "gate_refund": Noul(instructions="Should the `refund` skill be suggested?"),
            "gate_vpn": Noul(instructions="Should the `vpn` skill be suggested?"),
            "gate_billing": Noul(instructions="Should the `billing` skill be suggested?"),
        },
    )
    gates = [call1.nouls[f"gate_{s}"].noul for s in ("refund", "vpn", "billing")]
    if sum(gates) / len(gates) < 0.30:
        suggestions = []  # stay quiet
    else:
        top3 = sorted(("refund", "vpn", "billing"))[:3]
        call2 = client.system_one(
            state={"request": request_text, "shortlist": top3},
            questions={
                "pick": Choice(
                    instructions="Pick the best skill from `shortlist`.",
                    criteria={s: None for s in top3},
                ),
                **{f"fits_{s}": Noul(instructions=f"Does `{s}` fit `request`?")
                   for s in top3},
            },
        )
        suggestions = [s for s in top3 if call2.nouls[f"fits_{s}"].noul >= 0.30]
```
