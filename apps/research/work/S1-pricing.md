# S1 — Competitor Pricing Brief: AI Agent-Orchestration Platforms
**Scout:** S1 (angle: competitor pricing) | **Date verified:** 2026-09-20 (UTC)
**Goal context:** Monetizing an open-source framework + one production support-triage app, with Jev-gated supervision as differentiator vs LangGraph/CrewAI/AutoGen.
**Method:** websearch + webfetch of vendor pricing pages/docs on 2026-09-20. Every number below carries its source URL. Anything not verifiable is marked **UNSOURCED**.

---

## 1. LangSmith / LangChain (observability + deployment for LangGraph agents)

**Pricing model:** Seat subscription + dual usage meters (hybrid).
- Developer: `$0 / seat / month` ([source](https://www.langchain.com/pricing))
- Plus: `$39 / seat / month` ([source](https://www.langchain.com/pricing))
- Enterprise: `Custom pricing` ([source](https://www.langchain.com/pricing))
- Usage currencies: `LCU (LangChain Compute Unit) = $1.50 / LCU` ([source](https://www.langchain.com/pricing)) ; `LSU (LangChain Storage Unit) = $1.00 / LSU` ([source](https://www.langchain.com/pricing))
- Included traces: Developer `5,000 base traces / mo` ([source](https://www.langchain.com/pricing)) ; Plus `10,000 base traces / mo` ([source](https://www.langchain.com/pricing))
- Fleet allowance: Developer `5 LCU / mo` ([source](https://www.langchain.com/pricing)) ; Plus `25 LCU / mo` ([source](https://www.langchain.com/pricing))
- Sandbox allowance: `5 LCU ([source](https://www.langchain.com/pricing)) + 1 LSU / mo free ([source](https://www.langchain.com/pricing))` on both Developer and Plus
- Plus includes `1 free Serverless (Small) deployment ([source](https://www.langchain.com/pricing))`
- Overage trace list cited by secondary: base `$2.50 per 1k traces ([source](https://docs.langchain.com/langsmith/pricing-plans)) (14-day retention)` and extended `$5.00 per 1k ([source](https://docs.langchain.com/langsmith/pricing-plans)) (400-day)` — note live page now abstracts these into LSU; dollar-per-1k figures are from docs/secondary captures, treat current LSU conversion (`0.005 LSU per base trace ([source](https://www.usagepricing.com/blueprint/langsmith))` per secondary) as secondary-sourced ([source](https://www.usagepricing.com/blueprint/langsmith))
- Framework itself (LangChain / LangGraph): open-source, free — paid surface is LangSmith platform ([source](https://www.truefoundry.com/blog/langchain-pricing))

**Entry price point:** `$0 ([source](https://www.langchain.com/pricing))` (Developer, max `1 seat ([source](https://www.langchain.com/pricing))`). First paid step: `$39/seat/mo ([source](https://www.langchain.com/pricing)) + pay-as-you-go ([source](https://www.langchain.com/pricing))`.

**What the paid tier gates:**
- Plus gates: unlimited seats (vs `1 ([source](https://www.langchain.com/pricing))` on Developer) ([source](https://www.langchain.com/pricing)), Deployment / Engine / Sandboxes access ([source](https://www.langchain.com/pricing)), `10k ([source](https://www.langchain.com/pricing)) vs 5k traces ([source](https://www.langchain.com/pricing))`, email/support portal vs community-only ([source](https://www.langchain.com/pricing))
- Enterprise gates: self-hosted + hybrid deployment ([source](https://www.langchain.com/pricing)), custom SSO / ABAC / RBAC ([source](https://www.langchain.com/pricing)), support SLA ([source](https://www.langchain.com/pricing)), custom seats/workspaces + annual invoice ([source](https://www.langchain.com/pricing)), infosec review / custom terms ([source](https://www.langchain.com/pricing))
- Startup plan: discounted rates + `up to $10,000 in credits` ([source](https://www.langchain.com/pricing))

**UNSOURCED / gaps:** Exact current $/1k-trace overage on live LCU/LSU calculator is estimate-only (`Actual LCU/LSU consumption varies`) ([source](https://www.langchain.com/pricing)) — do not quote a fixed monthly bill without metering your trace/deployment mix. Enterprise dollar floor is **UNSOURCED** (custom only).

---

## 2. CrewAI / CrewAI AMP (framework + enterprise agent platform)

**Pricing model:** Free tier (hard-capped executions) + custom-quoted Enterprise with flexible overage. OSS framework free (MIT).
- Current public page: only two tiers — Basic `Free ([source](https://www.crewai.com/pricing))` and Enterprise `Custom ([source](https://www.crewai.com/pricing))` (mirror: ([source](https://crewai.com/pricing?sa=X)))
- Basic Free includes `50 workflow executions / month ([source](https://www.crewai.com/pricing))`, visual editor + AI copilot + GitHub integration ([source](https://www.crewai.com/pricing))
- Enterprise: `Custom ([source](https://www.usagepricing.com/blueprint/crewai))` pricing, executions `sized to workflow ([source](https://www.usagepricing.com/blueprint/crewai))` + `flexible overage ([source](https://www.usagepricing.com/blueprint/crewai))` (rate unpublished) ([source](https://www.usagepricing.com/blueprint/crewai))
- OSS self-host: `Free ([source](https://www.usagepricing.com/blueprint/crewai))`, MIT, no execution cap, BYO LLM keys ([source](https://www.usagepricing.com/blueprint/crewai))

**Entry price point:** `$0 ([source](https://www.crewai.com/pricing))` (Basic, `50 executions/mo ([source](https://www.crewai.com/pricing))`). First paid step is **custom Enterprise** — no self-serve paid price on live page ([source](https://www.crewai.com/pricing)).

**What the paid tier gates (Enterprise vs Basic):**
- Governance: SSO (MS Entra, Okta), RBAC, workload identity, PII redaction, policies — Enterprise-only ([source](https://crewai.com/pricing?sa=X))
- Deploy: CrewAI cloud vs customer VPC / own infra, Dedicated VPC, NAT, SAM certified, FedRAMP High — Enterprise-only ([source](https://crewai.com/pricing?sa=X))
- Scale/support: 45-day onboarding, forward-deployed engineers, dedicated Slack/Teams, on-site, training — Enterprise-only ([source](https://www.crewai.com/pricing))
- Observe/optimize (tracing, OpenTelemetry, guardrails, HITL, hallucination scores) listed as ✓ on both tiers on current page ([source](https://crewai.com/pricing?sa=X)) — i.e. NOT gated by current page; depth/SLA is the gate.

**Historical / secondary-only pricing (not on live page — do not present as current):**
- Professional `$25 / month ([source](https://www.usagepricing.com/blueprint/crewai))`, `100 executions/mo included ([source](https://www.usagepricing.com/blueprint/crewai))`, `+1 seat ([source](https://www.usagepricing.com/blueprint/crewai))`, overage `$0.50 / execution ([source](https://www.usagepricing.com/blueprint/crewai))` — existed Oct 2025 → removed spring 2026
- Login-gated tiers reported 2025–2026: Basic `$99/mo ([source](https://www.lindy.ai/blog/crew-ai-pricing)) (100 executions ([source](https://www.lindy.ai/blog/crew-ai-pricing)))`, Standard `$500/mo ([source](https://www.lindy.ai/blog/crew-ai-pricing)) (1,000 ([source](https://www.lindy.ai/blog/crew-ai-pricing)))`, Pro `$1,000/mo ([source](https://www.lindy.ai/blog/crew-ai-pricing)) (2,000 ([source](https://www.lindy.ai/blog/crew-ai-pricing)))`, Enterprise custom `(10,000 ([source](https://www.lindy.ai/blog/crew-ai-pricing)))` ; same ladder repeated ([source](https://aramb.ai/blog/crewai-pricing/))
- Enterprise annual reportedly `between $60,000 ([source](https://www.autolearningagents.com/crewai/crewai-enterprise.php)) and $120,000 annually ([source](https://www.autolearningagents.com/crewai/crewai-enterprise.php))` ; single-point claim `$60,000 per year ([source](https://www.zenml.io/blog/crewai-pricing)) (10,000 executions/mo ([source](https://www.zenml.io/blog/crewai-pricing)), 50 crews ([source](https://www.zenml.io/blog/crewai-pricing)))` — both secondary, **UNVERIFIED against primary**.
- Third-party aggregator claim `Enterprise from $299/mo ([source](https://aisotools.com/pricing/crewai))` — conflicts with live Custom-only page; mark **UNSOURCED / unreliable**.

**UNSOURCED / gaps:** Current Enterprise dollar floor, per-execution overage rate, and seat price are **UNSOURCED** (live page publishes no numbers beyond Free/50). LLM token cost is BYO pass-through — largest line for heavy users — amount **UNSOURCED** (depends on provider).

---

## 3. Relevance AI (AI Workforce — Actions + Vendor Credits dual meter)

**Pricing model:** Tiered subscription (org-level) + dual usage meters (Actions = work done; Vendor Credits = wholesale model cost, no markup) + top-ups.
- Free: `$0 / month ([source](https://relevanceai.com/pricing-new))`, `200 Actions / month ([source](https://relevanceai.com/pricing-new))` + `$2 bonus vendor credits ([source](https://relevanceai.com/pricing-new))` (marketing-page variant)
- Pro monthly: `$29 / month ([source](https://relevanceai.com/pricing-new))`, `2,500 Actions / month ([source](https://relevanceai.com/pricing-new))` + `$20 vendor credits / month ([source](https://relevanceai.com/pricing-new))`
- Pro annual: `$19 / month ([source](https://relevanceai.com/pricing-new))` (`33% off ([source](https://relevanceai.com/pricing-new))`), `30,000 Actions / year ([source](https://relevanceai.com/pricing-new))` + `$240 Vendor Credits / year ([source](https://relevanceai.com/pricing-new))` ; confirmed in docs: `Pro — $19/mo annual ([source](https://relevanceai.com/docs/get-started/pricing.md)), $29/mo monthly ([source](https://relevanceai.com/docs/get-started/pricing.md))`
- Team monthly: `$349 / month ([source](https://relevanceai.com/pricing-new))`, `7,000 Actions / month ([source](https://relevanceai.com/pricing-new))` + `$70 vendor credits / month ([source](https://relevanceai.com/pricing-new))`
- Team annual: `$234 / month ([source](https://relevanceai.com/pricing-new))` (`33% off ([source](https://relevanceai.com/pricing-new))`), `84,000 Actions / year ([source](https://relevanceai.com/pricing-new))` + `$840 Vendor Credits / year ([source](https://relevanceai.com/pricing-new))` ; confirmed ([source](https://relevanceai.com/docs/get-started/pricing.md))
- Price/year full-price comparison: Pro `$348 ([source](https://relevanceai.com/pricing-new))`, Team `$4,188 ([source](https://relevanceai.com/pricing-new))`
- Enterprise: `Custom ([source](https://relevanceai.com/pricing-new))` Actions + Custom credits ([source](https://relevanceai.com/pricing-new))
- Top-ups (paid plans only): `Extra Actions $80 per 1,000 ([source](https://relevanceai.com/docs/get-started/pricing.md))` ; `Extra Vendor Credits $20 per 10,000 ([source](https://relevanceai.com/docs/get-started/pricing.md))` ; increments: Actions in `1,000s ([source](https://relevanceai.com/docs/get-started/pricing.md))`, Credits in `10,000s ([source](https://relevanceai.com/docs/get-started/pricing.md))`
- Rollover: Vendor Credits roll over indefinitely while subscribed; plan Actions reset at renewal; purchased Action top-ups roll over ([source](https://relevanceai.com/docs/get-started/pricing.md))
- Quotas: Pro `2 Build Users ([source](https://relevanceai.com/docs/get-started/pricing.md))`, Team `5 Build Users ([source](https://relevanceai.com/docs/get-started/pricing.md)) · 45 End Users ([source](https://relevanceai.com/docs/get-started/pricing.md)) · 5 Shared Projects ([source](https://relevanceai.com/docs/get-started/pricing.md))` ; docs monthly Vendor Credits: Pro `10,000/mo (worth $20) ([source](https://relevanceai.com/docs/get-started/pricing.md))`, Team `35,000/mo (worth $70) ([source](https://relevanceai.com/docs/get-started/pricing.md))`

**Entry price point:** `$0 ([source](https://relevanceai.com/pricing-new))` Free (`200 Actions/mo ([source](https://relevanceai.com/pricing-new))`) where still available; first paid: Pro `$29/mo monthly ([source](https://relevanceai.com/pricing-new))` / `$19/mo annual ([source](https://relevanceai.com/pricing-new))`. **Change alert:** docs state `The Free plan is retired and closed to new signups` — existing Free orgs keep access ([source](https://relevanceai.com/docs/get-started/pricing.md)). Marketing page still renders Free — treat Free as legacy/transitional.

**What the paid tier gates:**
- Pro over Free: unlimited workforces (vs 1) ([source](https://relevanceai.com/pricing-new)), 2 build users, scheduling, Chat Mode, smart escalations, activity center, premium triggers (WhatsApp/LinkedIn/Telegram), BYO LLM, 90-day history ([source](https://relevanceai.com/docs/get-started/pricing.md))
- Team over Pro: 5 build + 45 end users, 5 shared projects, calling + meeting agents, A/B testing, analytics dashboard, priority support ([source](https://relevanceai.com/docs/get-started/pricing.md))
- Enterprise over Team: custom Actions/credits, unlimited users/projects, enterprise triggers (Salesforce/Snowflake/Zendesk), agent evaluations, work-hour controls, multi-org, SSO/RBAC/audit logs, dedicated AM, custom implementation ([source](https://relevanceai.com/docs/get-started/pricing.md))

**UNSOURCED / gaps:** Enterprise floor is **UNSOURCED** (custom). Per-run cost beyond top-up math is workload-dependent — **UNSOURCED** until Action-per-ticket measured.

---

## 4. Lindy (per-seat AI teammate, credit pool)

**Pricing model:** Per-seat subscription + pooled credits (no overage billing — pauses on exhaustion).
- Plus: `$29.99 / mo per user ([source](https://www.lindy.ai/pricing))`, `3k credits / user / mo ([source](https://www.lindy.ai/pricing))`
- Pro: `$99.99 / mo per user ([source](https://www.lindy.ai/pricing))`, `15k credits / user / mo ([source](https://www.lindy.ai/pricing)) (5x Plus ([source](https://www.lindy.ai/pricing)))`
- Max: `$199.99 / mo per user ([source](https://www.lindy.ai/pricing))`, `35k credits / user / mo ([source](https://www.lindy.ai/pricing)) (~12x Plus ([source](https://www.lindy.ai/pricing)))`
- Enterprise: custom — Everything in Max + HIPAA + signed BAA, shared usage + bonus credits, dedicated support, audit logs, onboarding ([source](https://www.lindy.ai/pricing))
- Pooling: every seat adds allocation to one shared workspace pool ([source](https://www.lindy.ai/pricing))
- No surprise bills: on exhaustion Lindy pauses credit-using actions until reset; upgrade to resume ([source](https://www.lindy.ai/pricing))
- No rollover: credits refresh each cycle, `don't roll over` ([source](https://www.lindy.ai/pricing))
- Credit burn examples: Everyday asks `2–250 credits ([source](https://www.lindy.ai/pricing))`, Deep work `250–1,000 ([source](https://www.lindy.ai/pricing))`, Big builds `1,000–2,500 ([source](https://www.lindy.ai/pricing))`
- Trial: `7-day free trial ([source](https://www.lindy.ai/pricing))` (Slack-joined teammates get first week free; direct signups billed right away) ([source](https://www.lindy.ai/pricing)) ; no permanent free tier on live page ([source](https://www.lindy.ai/pricing))

**Entry price point:** `$29.99 / user / mo ([source](https://www.lindy.ai/pricing))` (Plus, `3k credits ([source](https://www.lindy.ai/pricing))`).

**What the paid tier gates:**
- Higher tiers gate only credit volume + heavy-workload headroom (`3k ([source](https://www.lindy.ai/pricing)) → 15k ([source](https://www.lindy.ai/pricing)) → 35k ([source](https://www.lindy.ai/pricing))`); feature list (Slack-native, routines, 40+ skills, meeting library, inbox, computer use, MCP, model selection, approvals) shown as included out-of-the-box, not tier-split ([source](https://www.lindy.ai/pricing))
- Enterprise gates: HIPAA/BAA, audit logs, SSO (via security review), shared/bonus credits, dedicated support + onboarding ([source](https://www.lindy.ai/pricing))

**Conflicts / secondary-only (do not use as primary):**
- Coworker/CostBench report entry `$49.99/mo ([source](https://plg.coworker.ai/blog/lindy-ai-pricing))`, range `$49.99–$199.99/mo ([source](https://plg.coworker.ai/blog/lindy-ai-pricing)) ([source](https://costbench.com/software/ai-automation/lindy))`, no free plan ([source](https://plg.coworker.ai/blog/lindy-ai-pricing)) — conflicts with live `$29.99 Plus ([source](https://www.lindy.ai/pricing))`. Treat $49.99 as **superseded/secondary**; live page wins. Restructure history (Free `400 credits ([source](https://plg.coworker.ai/blog/lindy-ai-pricing))` → Starter `$19.99/2k ([source](https://plg.coworker.ai/blog/lindy-ai-pricing))` → Pro `$49.99/5k ([source](https://plg.coworker.ai/blog/lindy-ai-pricing))` → current Plus/Pro/Max) described ([source](https://plg.coworker.ai/blog/lindy-ai-pricing)) — secondary only.
- Older guide: Free `400 credits ([source](https://www.miniloop.ai/blog/lindy-ai-pricing-2026))`, Pro `$49/mo ([source](https://www.miniloop.ai/blog/lindy-ai-pricing-2026)) 5,000 credits ([source](https://www.miniloop.ai/blog/lindy-ai-pricing-2026))`, Business `$299/mo ([source](https://www.miniloop.ai/blog/lindy-ai-pricing-2026)) 30,000 ([source](https://www.miniloop.ai/blog/lindy-ai-pricing-2026))` — dated Jan 2026, superseded.

**UNSOURCED / gaps:** Annual discount (if any) is **UNSOURCED** (live page shows monthly only). Enterprise floor **UNSOURCED**. Overage $/credit **UNSOURCED** (model is pause-not-overage).

---

## 5. Gumloop (credit-pool automation; unlimited seats)

**Pricing model:** Flat subscription for credit pool (no per-seat charge) + 8% orchestration fee + capped overage.
- Pro: `Starts at $37 / month ([source](https://www.gumloop.com/pricing?plan=pro))`, `20,000 credits / month ([source](https://www.gumloop.com/pricing?plan=pro))` ; breakdown `7,400 + 12,600 bonus credits ([source](https://docs.gumloop.com/core-concepts/credits)) (20,000/mo ([source](https://docs.gumloop.com/core-concepts/credits)))`
- Free (transitional): `$0 ([source](https://agentdex.vercel.app/gumloop-pricing))`, `5,000 credits/mo ([source](https://agentdex.vercel.app/gumloop-pricing)), 1 seat ([source](https://agentdex.vercel.app/gumloop-pricing))` per June-2026 capture ; alternate capture: `Free 5k/mo ([source](https://gumloop.com/pricing)), 1 seat ([source](https://gumloop.com/pricing)), 1 trigger ([source](https://gumloop.com/pricing)), 2 concurrent runs ([source](https://gumloop.com/pricing))` — BUT Aug-2026 docs state `Every new account starts with a 14-day free trial of Pro ([source](https://docs.gumloop.com/core-concepts/credits))` (card required, one-time, rolls to paid unless cancelled) and Aug-2026 analysis confirms permanent Free removed from pricing page ~2026-07-30 ([source](https://plg.coworker.ai/blog/gumloop-pricing)). Treat Free as **removed/transitional**.
- Enterprise: `Custom pricing ([source](https://docs.gumloop.com/core-concepts/credits))`, custom credits + `unused credits roll over ([source](https://docs.gumloop.com/core-concepts/credits))` (vs no rollover on Pro)
- Credit value: `$1 buys 200 credits ([source](https://docs.gumloop.com/core-concepts/credits))` i.e. `1 credit = $0.005 ([source](https://docs.gumloop.com/core-concepts/credits))`
- Overage: must enable; billed at `$0.005 per credit ([source](https://docs.gumloop.com/core-concepts/credits))`, Pro capped at `1,000,000 overage credits / period ([source](https://docs.gumloop.com/core-concepts/credits)) ($5,000 ([source](https://docs.gumloop.com/core-concepts/credits)))` default
- Orchestration fee: `8% ([source](https://docs.gumloop.com/core-concepts/credits)) of (Chat & Reasoning + Compute + Tool Calls)` on Pro ; `discounts available` on Enterprise ([source](https://www.gumloop.com/pricing?plan=pro)) ; BYOK raises fee to `16% ([source](https://docs.gumloop.com/core-concepts/credits))` while zeroing Chat & Reasoning credits ([source](https://docs.gumloop.com/core-concepts/credits))
- Compute: `5 credits per session-minute ([source](https://docs.gumloop.com/core-concepts/credits))` (min `1/response ([source](https://docs.gumloop.com/core-concepts/credits))`; VPC Enterprise not charged compute)
- Tool calls: `1 credit per successful call ([source](https://docs.gumloop.com/core-concepts/credits)) + tool's own charge` (e.g. enrichment extra)
- Seats/teams: `Unlimited ([source](https://www.gumloop.com/pricing?plan=pro))` on Pro and Enterprise ; concurrency Pro `5 runs ([source](https://gumloop.com/pricing)) / 25 agent chats ([source](https://gumloop.com/pricing))`
- Slider history: Pro scaled `$37 (20k) ([source](https://www.usagepricing.com/blueprint/gumloop)) → $1,840 (1M) ([source](https://www.usagepricing.com/blueprint/gumloop))` before Enterprise custom ; Aug-2026 change flattened to `$37 flat ([source](https://www.usagepricing.com/blueprint/activity/gumloop-2026-08-26-flat-pro-orchestration-fee))`, no annual option + added `8% fee ([source](https://www.usagepricing.com/blueprint/activity/gumloop-2026-08-26-flat-pro-orchestration-fee))` + recapped overage ([source](https://www.usagepricing.com/blueprint/activity/gumloop-2026-08-26-flat-pro-orchestration-fee))

**Entry price point:** `$37 / month ([source](https://docs.gumloop.com/core-concepts/credits))` (Pro, `20k credits ([source](https://docs.gumloop.com/core-concepts/credits))`) + `14-day trial ([source](https://docs.gumloop.com/core-concepts/credits))`. Legacy free `$0 / 5k ([source](https://agentdex.vercel.app/gumloop-pricing))` no longer on live page — see above.

**What the paid tier gates:**
- Pro over (former) Free: unlimited seats/teams + unified billing, 5 concurrent runs / 25 chats, team usage/analytics, MCP hosting, connector policies (agent-scoped) ([source](https://gumloop.com/pricing))
- Enterprise over Pro: RBAC, SCIM/SAML, admin dashboard, audit logs, custom retention, security reports, data exports, incognito, model access control, VPC, queuing, org-wide guardrails, Insights dashboard (Enterprise feature) ([source](https://gumloop.com/pricing)) ([source](https://docs.gumloop.com/core-concepts/credits))

**UNSOURCED / gaps:** Enterprise floor and negotiated orchestration discount are **UNSOURCED**. Annual discount (`20% OFF ([source](https://gumloop.com/pricing))` toggle) appears on one capture ([source](https://gumloop.com/pricing)) but Aug-2026 capture says annual option removed ([source](https://www.usagepricing.com/blueprint/activity/gumloop-2026-08-26-flat-pro-orchestration-fee)) — treat annual as **UNSOURCED / transitional**.

---

## Monetization takeaways (for OS framework + support-triage app, Jev-gated supervision)

1. **Hybrid seat + usage is the norm, not the exception.** LangSmith (`$39/seat ([source](https://www.langchain.com/pricing)) + LCU $1.50 ([source](https://www.langchain.com/pricing))/LSU $1.00 ([source](https://www.langchain.com/pricing))`), Lindy (`$29.99–$199.99/user ([source](https://www.lindy.ai/pricing)) + pooled credits, pause-not-overage ([source](https://www.lindy.ai/pricing))`), Relevance (`$29/$349 ([source](https://relevanceai.com/docs/get-started/pricing.md)) + Actions $80/1k ([source](https://relevanceai.com/docs/get-started/pricing.md)) + Credits $20/10k ([source](https://relevanceai.com/docs/get-started/pricing.md))`), Gumloop (`$37 ([source](https://docs.gumloop.com/core-concepts/credits)) + $0.005/credit ([source](https://docs.gumloop.com/core-concepts/credits)) + 8% fee ([source](https://docs.gumloop.com/core-concepts/credits))`). A Jev-gated triage app can price the same way: per-seat platform fee + per-triage meter, with supervision level as the value lever.
2. **Gate governance, not building.** All five gate SSO/RBAC/audit/VPC/SLA/DPA on Enterprise/custom ([sources](https://www.langchain.com/pricing) ([source](https://crewai.com/pricing?sa=X)) ([source](https://relevanceai.com/docs/get-started/pricing.md)) ([source](https://www.lindy.ai/pricing)) ([source](https://gumloop.com/pricing)). Keep framework + visual builder + tracing open; charge for Jev policy controls (PII redaction, approval queues, audit, retention) — direct parallel to CrewAI Enterprise governance ([source](https://crewai.com/pricing?sa=X)) and LangSmith Enterprise security ([source](https://www.langchain.com/pricing)).
3. **Free is a funnel with a hard cap, and it is shrinking.** Caps: `5k traces ([source](https://www.langchain.com/pricing))` (LangSmith), `50 executions ([source](https://www.crewai.com/pricing))` (CrewAI), `200 Actions ([source](https://relevanceai.com/docs/get-started/pricing.md))` (Relevance, now retired for new signups), trial-only ([source](https://www.lindy.ai/pricing)) (Lindy), `14-day trial ([source](https://docs.gumloop.com/core-concepts/credits))` (Gumloop). Do not promise perpetual generous free; promise time-boxed production pilot with measured Action/trace burn.
4. **Differentiator pricing:** Jev-gated supervision maps to the most expensive meters (human review, evals, Engine-like auto-fix at `~5–30 LCU/run ([source](https://www.langchain.com/pricing))` secondary estimate — actually bill supervision as premium tier (e.g. Standard auto-triage vs Supervised triage with eval + approval), mirroring Relevance calling/meeting agents gated to Team ([source](https://relevanceai.com/docs/get-started/pricing.md)) and Lindy Max for heaviest workloads ([source](https://www.lindy.ai/pricing)).
5. **Avoid the mid-tier trap CrewAI just exited.** CrewAI deleted its `$25 ([source](https://www.usagepricing.com/blueprint/crewai))` Professional bridge and unpublished its `$0.50 overage ([source](https://www.usagepricing.com/blueprint/crewai))`, collapsing to Free + Custom ([source](https://www.usagepricing.com/blueprint/crewai)). Prefer 2–3 rungs (Free/trial → Pro seat+pool → Enterprise custom) over 5 execution ladders that force upgrades every 2x volume.

## Source list (primary first)
- https://www.langchain.com/pricing
- https://docs.langchain.com/langsmith/pricing-plans
- https://www.crewai.com/pricing
- https://crewai.com/pricing?sa=X
- https://relevanceai.com/pricing-new
- https://relevanceai.com/docs/get-started/pricing.md
- https://relevanceai.com/docs/admin/subscriptions/new-pricing.md
- https://www.lindy.ai/pricing
- https://docs.gumloop.com/core-concepts/credits
- https://www.gumloop.com/pricing?plan=pro
- https://gumloop.com/pricing
- Secondaries: https://www.usagepricing.com/blueprint/langsmith, https://www.usagepricing.com/blueprint/crewai, https://www.usagepricing.com/blueprint/gumloop, https://www.usagepricing.com/blueprint/activity/gumloop-2026-08-26-flat-pro-orchestration-fee, https://plg.coworker.ai/blog/lindy-ai-pricing, https://plg.coworker.ai/blog/gumloop-pricing, https://www.lindy.ai/blog/crew-ai-pricing, https://aramb.ai/blog/crewai-pricing/, https://costbench.com/software/ai-automation/lindy, https://agentdex.vercel.app/gumloop-pricing, https://www.autolearningagents.com/crewai/crewai-enterprise.php, https://www.zenml.io/blog/crewai-pricing, https://aisotools.com/pricing/crewai, https://www.miniloop.ai/blog/lindy-ai-pricing-2026
