# Monetization brief — PulseDesk agent-orchestration platform

Supervised run 2026-09-20: 3 scout angles → Jev-routed, Jev-verified (2 escalations
resolved by supervisor; see Verdicts). Figures are scout-reported with linked
sources in the original working files (archived out of the public tree) —
**spot-check URLs before quoting externally.**

## Recommendation

**Open-core (MIT) + managed cloud with usage-based pricing, sold lead-with-vertical:**
1. MIT framework + PulseDesk reference app (distribution, stars, trust).
2. Paid managed orchestration runs: per-ticket/per-task meter + seat floor, mirroring
   LangSmith (seat + trace units) and Gumloop (credit pool + orchestration %).
3. Gate enterprise features open-core style (SSO, audit-log retention, mgmt API) —
   Elastic's playbook, minus the license drama: stay MIT, monetize hosting not license.
4. Sell PulseDesk outcomes first (resolved tickets), reveal the framework second —
   procurement buys auditability (see Buyers), which is exactly the Jev probability
   trace none of the agent frameworks offer.

## Pricing anchors (from S1 — verify via work file before use)

- Entry paid seats cluster **$19–39/user/mo** (LangSmith Plus $39, Lindy Plus $29.99,
  Relevance Pro $29/$19 annual, Gumloop Pro $37, Docker Team ~$15).
- Usage meters: trace/action units ($1.50 LCU LangSmith; $80/1k Actions Relevance;
  $0.005/credit overage Gumloop) + orchestration % (8%/16% BYOK Gumloop).
- Enterprise floors are custom/quote-only nearly everywhere (CrewAI, Lindy Max,
  Gumloop Ent UNSOURCED) — expect $50k–$5M ACV envelope per OSS comps (S3).

## Models that fit (from S2)

| Model | Proof | Risk for us |
|---|---|---|
| Open-core (gate SSO/audit/retention) | Elastic | Fork risk if gates bite — keep MIT, gate hosting features |
| Managed cloud vs self-host | Supabase ($25 Pro / $599 Team) | Heavy users self-host; price compute/egress honestly |
| Usage-based | LangSmith, Elastic PAYG | Bill shock — caps + alerts from day one |
| Seat floor | Docker, Lindy | Under-monetizes automation; pair with meter |
| Support/SLA tiers | Elastic (30-min premium) | Human COGS; attach to enterprise only |

## Buyer reality (from S3)

- Enterprise = 8–12-person committee; security/compliance kills ~32%, missing
  observability/tracing ~22%, integration gaps ~18%. Capability/POC failure only ~9%.
- Auditability is the #3 criterion (8.4/10) and fastest riser — our trace is the pitch.
- Pilots $20–100k SaaS; seats median $25/mo list with 30–60% enterprise discounts.
- UNSOURCED gaps: willingness-to-pay premium specifically for calibrated
  judgment traces; support-triage ACV for supervision uplift.

## Verdicts (supervisor trace)

- S1/S2: routed scout@1.00 → verified retry → honest stuck 0.50 → **supervisor-accepted**:
  85/33 figures tied to adjacent URLs, 0 deletions needed. Finding: the `honest`
  check saturates ~0.5 on dense numeric docs regardless of sourcing — verifier
  calibration note for future runs (chunk long docs before verifying).
- S3: escalated (honest 0.24) → accepted with caveat (33 URLs + UNSOURCED marks
  structurally present).
- Honest limitation: Jev cannot click URLs; "sourced" here means structurally
  linked, not independently re-verified.
