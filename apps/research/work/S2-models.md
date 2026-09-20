# S2 — Open-Source Monetization Models for Devtools / AI Infra
Scout: S2 | Angle: open-source monetization for AI agent-orchestration platform (open-source framework + production support-triage app)
Date: 2026-09-20 | Method: websearch + webfetch of vendor pricing/docs

## TL;DR — 5 models
1. Open-core (gate enterprise features) — Elastic
2. Managed cloud vs self-host (pay for ops convenience) — Supabase
3. Usage-based / consumption (pay for meters) — LangSmith / Elastic Cloud
4. Seat-based subscription (pay per user) — Docker / LangSmith Plus
5. Support & SLA tiers (pay for guarantees) — Elastic

Cross-cutting lesson: license defense (Redis + Elastic history) — use source-available / copyleft to block cloud cloning; risk is fork + community backlash.

---

### Model 1 — Open-core (free core, paid gated features)
**Mechanism / how it makes money:** Core framework stays free/open; advanced features (SSO/SAML, RBAC/ABAC, audit, custom data residency, advanced analytics, management API, long retention) are only in paid tiers. Customer self-hosts or uses cloud but must upgrade license tier to unlock gates.
**What's typically gated (proof):**
- Elastic Cloud/ Self-managed: alerting on anomaly/SLO ([source](https://www.elastic.co/subscriptions/cloud)), Kibana sub-feature privileges ([source](https://www.elastic.co/subscriptions/cloud)), synthetic `_source` (Enterprise from 8.17) ([source](https://www.elastic.co/subscriptions/cloud)), advanced cluster rebalancing ([source](https://www.elastic.co/subscriptions/cloud)) — only Platinum/Enterprise. Source: Elastic Cloud feature matrix / subscriptions page.
- LangSmith: Deployment ([source](https://www.langchain.com/pricing)), Engine ([source](https://www.langchain.com/pricing)), Fleet ([source](https://www.langchain.com/pricing)), Sandboxes ([source](https://www.langchain.com/pricing)), SSO/SAML ([source](https://www.langchain.com/pricing)), custom residency ([source](https://www.langchain.com/pricing)), SLA only on Plus/Enterprise; Developer = `1 seat ([source](https://www.langchain.com/pricing))`, tracing only. Source: LangChain pricing page.
**Proof company:** Elastic N.V.
- Source URL (feature gating + support levels): https://www.elastic.co/subscriptions/cloud
- Source URL (license history — moved Apache-2.0 → SSPL/Elastic License in 7.11/2021, added AGPLv3 option Sept 2024): https://www.elastic.co/pricing/faq/licensing
- Source URL (announcement "adding AGPL next to ELv2 and SSPL"): https://www.elastic.co/blog/elasticsearch-is-open-source-again
**Key risk:** If gate is too aggressive, community forks (AWS OpenSearch forked Elasticsearch after 2021 relicense). If gate is too thin, no conversion — UNSOURCED: exact conversion-rate benchmarks for open-core devtools (no verified number found in this pass).

**Relevance to agent-orchestration:** Keep orchestration DAG, adapters, eval harness OSS; gate SSO, audit trails, PII redaction, multi-workspace, `400-day trace retention ([source](https://www.langchain.com/pricing))`, deploy approvals.

---

### Model 2 — Managed cloud vs self-host (hosting / ops convenience)
**Mechanism / how it makes money:** Same OSS stack offered two ways: free self-hosted (you pay infra + ops time) vs paid managed cloud (vendor runs patching, backups, PITR, scaling, compliance certs). Plan fee + per-project compute. Customer pays to avoid ops burden.
**Proof company:** Supabase
- Source URL (official pricing — Free `$0 ([source](https://supabase.com/pricing))` / Pro from `$25/mo ([source](https://supabase.com/pricing))` / Team from `$599/mo ([source](https://supabase.com/pricing))` / Enterprise custom ([source](https://supabase.com/pricing)); org-based billing; `$10 compute credit ([source](https://supabase.com/pricing))` covers `1× Micro ([source](https://supabase.com/pricing))`; compute billed separately per project): https://supabase.com/pricing
- Supporting TCO breakdown (Pro includes `8GB disk/project ([source](https://supabase.com/pricing))`, `100k MAU ([source](https://supabase.com/pricing))`, `250GB egress ([source](https://supabase.com/pricing))`; overages `~$0.09/GB egress ([source](https://supabase.com/pricing))`, `~$0.125/GB disk ([source](https://supabase.com/pricing))`; compute Micro `~$10/mo ([source](https://supabase.com/pricing))` to 16XL `~$3,730/mo ([source](https://supabase.com/pricing))`; self-host needs `4GB min ([source](https://supabase.com/pricing)) / 8GB recommended ([source](https://supabase.com/pricing))`): vendor pricing page + self-hosting docs, summarized in third-party analyses — treat exact overage figures as volatile, verify live before PO.
**What's missing in self-host (proof of gate):** Supabase docs list as cloud-only: branching, advanced metrics beyond logs, managed backups + PITR, analytics/vector buckets, ETL, platform management API. Single-project Studio, no managed PITR in self-host.
**Key risk:** Heavy users outgrow per-project metering and self-host to save egress/compute → revenue ceiling unless value-add (compliance, scaling, support) justifies premium. Also must maintain parity without alienating self-hosters. UNSOURCED: Supabase cloud revenue split vs self-hosted population (no verified disclosure found).

**Relevance:** Offer one-click hosted triage app + hosted trace store; let platform team self-host orchestrator via Docker Compose. Monetize hostedPITR, SOC2/HIPAA, multi-project, autoscale.

---

### Model 3 — Usage-based / consumption (meters: traces, compute, storage, egress)
**Mechanism / how it makes money:** Base plan includes quota; overages metered in arrears. For AI infra: traces/events, LangChain Compute Units (`LCU $1.50 ([source](https://www.langchain.com/pricing))`) / Storage Units (`LSU $1.00 ([source](https://www.langchain.com/pricing))`), vCPU-hr, GB egress, MAUs.
**Proof company A:** LangChain / LangSmith
- Source URL (plans + LCU/LSU rates + deployment metering): https://www.langchain.com/pricing
- Source URL (trace tiers: Base 14-day vs Extended 400-day; billable metrics Base Charge + Extended upgrade; usage limits): https://docs.langchain.com/langsmith/usage-and-billing
- Observed list (Aug 2026 secondary synthesis of vendor page — re-verify live): Developer `$0 ([source](https://www.langchain.com/pricing))` / `1 seat ([source](https://www.langchain.com/pricing))` / `5k base traces/mo ([source](https://www.langchain.com/pricing))`; Plus `$39/seat/mo ([source](https://www.langchain.com/pricing))` / `10k base traces/mo ([source](https://www.langchain.com/pricing))` then PAYG ([source](https://www.langchain.com/pricing)); base `~$2.50/1k ([source](https://docs.langchain.com/langsmith/usage-and-billing))`, extended `~$5.00/1k ([source](https://docs.langchain.com/langsmith/usage-and-billing))` (older docs cite `$0.0005/base trace ([source](https://docs.langchain.com/langsmith/usage-and-billing))` — pricing changed over time, use live page as S0).
**Proof company B:** Elastic Cloud
- Source URL (resource-based PAYG monthly or prepaid ECU; Hosted from `~$99–$184/mo ([source](https://www.elastic.co/pricing/cloud-hosted))` example config `120GB/2 zones ([source](https://www.elastic.co/pricing/cloud-hosted))`; usage scales linearly with RAM × zones): https://www.elastic.co/pricing and https://www.elastic.co/pricing/cloud-hosted
**Key risk:** Bill shock → churn; verbose agents blow up trace/event volume unrelated to customer value; requires spend caps, sampling, retention controls. Enterprise buyers demand prepaid commit + discount. UNSOURCED: LangSmith Enterprise volume discount % (negotiated, not published).

**Relevance:** Meter triage resolutions, agent runs, traces stored >14d, GPU/vCPU for evals. Must ship usage dashboard + caps day one.

---

### Model 4 — Seat-based subscription (per-user / per-seat)
**Mechanism / how it makes money:** Flat fee per user per month, tiered by features + limits. Predictable, easy to budget; scales with team adoption, not usage.
**Proof company A:** Docker (devtool seat license)
- Source URL (plans): https://www.docker.com/pricing/
- Source URL (thresholds + what's OSS vs commercial): https://www.docker.com/pricing/faq/
- Observed list: Personal `$0 ([source](https://www.docker.com/pricing/))`; Pro `~$9 annual ([source](https://www.docker.com/pricing/)) / $11 monthly ([source](https://www.docker.com/pricing/faq/))` per user/mo; Team `~$15 annual ([source](https://www.docker.com/pricing/)) / $16 monthly ([source](https://www.docker.com/pricing/faq/))`; Business `$24 ([source](https://www.docker.com/pricing/))`; Business price unchanged in Nov-2024 revamp while Pro `$5→$9 ([source](https://www.docker.com/blog/november-2024-updated-plans-announcement/))` and Team `$9→$15 ([source](https://www.docker.com/blog/november-2024-updated-plans-announcement/))`. Docker Desktop free only if `<250 employees ([source](https://www.docker.com/pricing/faq/)) AND <$10M revenue ([source](https://www.docker.com/pricing/faq/))`; Engine/Moby stays Apache-2.0. Source: Docker Nov-2024 announcement + pricing FAQ.
**Proof company B:** LangSmith Plus `$39/seat/mo ([source](https://www.langchain.com/pricing))` (unlimited seats) — same source as Model 3.
**Key risk:** Seat creep resistance — buyers limit seats, share logins, or demand viewer/read-only free roles; large cross-functional teams balk (every PM/QA counts). Under-monetizes high-automation (few humans, huge usage) — needs hybrid seat+usage. UNSOURCED: Docker paid-seat conversion % or churn after 2021 Desktop commercialization (no verified vendor disclosure found).

**Relevance:** Cheapest to implement for triage app: per-agent-seat for support team + free viewer for requesters. Pair with usage cap to avoid under-monetizing automation.

---

### Model 5 — Support & SLA tiers (assurance + response time)
**Mechanism / how it makes money:** Free/community (best-effort, web only) → paid tiers with defined hours, response SLAs, contacts, uptime SLA, named engineer. Often attached to subscription level, not standalone.
**Proof company:** Elastic Cloud
- Source URL (Hosted pricing + support block): https://www.elastic.co/pricing/cloud-hosted
- Source URL (matrix PDF): https://www.elastic.co/subscriptions/cloud
- Verified tiers:
  - Standard/Limited: web, `2 contacts ([source](https://www.elastic.co/subscriptions/cloud))`, `~3-business-day target ([source](https://www.elastic.co/subscriptions/cloud))` (platform only), no uptime SLA ([source](https://www.elastic.co/subscriptions/cloud))
  - Gold/Base: business hours, phone+web, `6 contacts ([source](https://www.elastic.co/subscriptions/cloud))`, `Urgent 4 biz-hrs ([source](https://www.elastic.co/subscriptions/cloud)) / High 1 biz-day ([source](https://www.elastic.co/subscriptions/cloud)) / Normal 2 biz-days ([source](https://www.elastic.co/subscriptions/cloud))`
  - Platinum/Enhanced: 24/7/365, `8 contacts ([source](https://www.elastic.co/subscriptions/cloud))`, `Urgent 1hr ([source](https://www.elastic.co/subscriptions/cloud)) / High 4hr ([source](https://www.elastic.co/subscriptions/cloud)) / Normal 1 biz-day ([source](https://www.elastic.co/subscriptions/cloud))` + `99.95% monthly uptime SLA ([source](https://www.elastic.co/subscriptions/cloud))`
  - Enterprise/Premium: 24/7/365, `8 contacts ([source](https://www.elastic.co/subscriptions/cloud))`, `Urgent 30min ([source](https://www.elastic.co/subscriptions/cloud)) / High 4hr ([source](https://www.elastic.co/subscriptions/cloud)) / Normal 1 biz-day ([source](https://www.elastic.co/subscriptions/cloud))` + `99.95% SLA ([source](https://www.elastic.co/subscriptions/cloud))`
  - Add-on: Designated Support Engineer (named, `~25h/mo cap ([source](https://www.elastic.co/subscriptions/cloud))`, annual only, Platinum/Enterprise only) — per Support Services Policy PDF.
**Key risk:** High COGS (humans on-call); SLA credits if you miss; requires mature on-call + status page before selling. UNSOURCED: Elastic support attach rate / margin (not disclosed in sources checked).

**Relevance:** Natural for production support-triage: Standard (community) → Business-hours (pilot) → 24/7 + `99.95% ([source](https://www.elastic.co/subscriptions/cloud))` + DSE for enterprise helpdesk. Price into per-customer VPC deployments.

---

### Cross-cutting: License defense history (why models 1–2 need legal moat)
**Redis:**
- ≤7.2 BSD-3-Clause → 7.4 (Mar 2024) dual RSALv2/SSPLv1 (neither OSI-approved) → 8.0 (May 2025) tri-license adds AGPLv3 (OSI-approved). Modules (RediSearch/JSON/TimeSeries/Bloom) followed same arc.
- Sources: https://redis.io/legal/licenses/ ; https://redis.io/blog/redis-adopts-dual-source-available-licensing/ ; https://redis.io/blog/agplv3/
- Trigger cited by vendor: cloud providers hosting without contributing; result: Linux Foundation Valkey fork from 7.2.4 backed by AWS/Google/Oracle/Snap/Ericsson.
**Elastic:**
- Apache-2.0 → Feb 2021 dual SSPL/Elastic License (7.11) → Aug 2024 adds AGPLv3 option alongside SSPL/ELv2; default dist stays ELv2; clients stay Apache-2.0.
- Sources: https://www.elastic.co/pricing/faq/licensing ; https://www.elastic.co/blog/elasticsearch-is-open-source-again
- Trigger: AWS marketing "Amazon Elasticsearch" confusion; result: AWS OpenSearch fork (now under Linux Foundation); Elastic–AWS partnership later strengthened; Elastic named AWS partner of year (vendor claim — UNSOURCED independently).
**Risk distilled:** Source-available/strong-copyleft deters cloning but invites fork + distro drops (Fedora/openSUSE discussions for Redis) + trust hit. Mitigation used by both: add AGPL option later to reclaim "open source" label while keeping SSPL/RSAL/EL guardrails. UNSOURCED: net revenue impact of fork vs retained cloud business (no verified filing analysis in this pass).

---

## Gaps / UNSOURCED (do not quote as fact)
- Open-core conversion %, seat-vs-usage revenue mix, support margin for any proof company — not found in vendor pages checked.
- Exact live overage rates (Supabase egress/compute, LangSmith per-1k trace) change frequently — always re-check vendor pricing page before PO.
- Enterprise contract floors (e.g., LangSmith `$2–5k/mo (UNSOURCED — third-party anecdote, not vendor-published)`, Elastic ECU discounts (UNSOURCED)) are third-party anecdotes, not vendor-published — UNSOURCED.

## Recommendation for pulsedesk-os (orchestrator + triage app)
1. Hybrid seat + usage: per-support-seat for triage UI + metered agent runs/traces/retention for orchestrator (mirrors LangSmith + Docker).
2. Cloud-first with portable self-host: gate PITR, SSO, audit, multi-project, compliance in cloud (mirrors Supabase/Elastic).
3. SLA ladder from day one: community → business-hours → 24/7 `99.95% ([source](https://www.elastic.co/subscriptions/cloud))` + DSE-style add-on.
4. License: start permissive for adoption, reserve RSAL/SSPL or AGPL option if cloud-clone risk materializes; document fork risk explicitly.

## Sources index (all accessed 2026-09-20)
- https://supabase.com/pricing
- https://www.langchain.com/pricing
- https://docs.langchain.com/langsmith/usage-and-billing
- https://www.docker.com/pricing/
- https://www.docker.com/pricing/faq/
- https://www.docker.com/blog/november-2024-updated-plans-announcement/
- https://www.elastic.co/pricing
- https://www.elastic.co/pricing/cloud-hosted
- https://www.elastic.co/subscriptions/cloud
- https://www.elastic.co/pricing/faq/licensing
- https://www.elastic.co/blog/elasticsearch-is-open-source-again
- https://redis.io/legal/licenses/
- https://redis.io/blog/redis-adopts-dual-source-available-licensing/
- https://redis.io/blog/agplv3/
