# Hackathon Diary

Running log of decisions, feedback, actions, and status from the Nevermined Autonomous Business Hackathon (March 5-6, 2026).

Written by: Mattie, Scav (director Claude), ScavieFae (autonomous worker via simple-loop)

---

## Format

Each entry is timestamped. Tag the source.

- **[mattie]** — decisions, observations, feedback from the venue
- **[scav]** — director evaluations, research findings, coordination notes
- **[scaviefae]** — automated entries from conductor/worker (brief status, blockers, completions)
- **[decision]** — explicit decision point (bold the choice made)
- **[blocker]** — something that's blocking progress
- **[feedback]** — input from other teams, judges, Nevermined staff

---

## March 5 (Thursday)

### 09:30 — Doors Open

**[scav]** Project state: all planning docs complete, zero code. Hackathon repo analyzed — the `mcp-server-agent` from nevermined-io/hackathons is 90% of our Phase 1 seller. `PaymentsMCP` handles OAuth, token validation, credit redemption. One decorator per tool.

**[decision]** Phase 1 strategy: fork mcp-server-agent, swap DuckDuckGo for Exa, register agent+plan, get first transaction. **Do not build the two-tool gateway yet.** Gateway is Phase 2 after the 8PM deadline.

**[blocker]** Need two Nevermined API keys (builder + subscriber) from https://nevermined.app before any code can transact. Mattie getting these at the venue.

### ~10:00 — Keys Coming In

**[mattie]** Exa API key obtained.

**[blocker]** Still need NVM_API_KEY (builder) and NVM_SUBSCRIBER_API_KEY (subscriber) from Nevermined. These gate setup.py and first transaction.

### ~12:30 — Keys Acquired

**[mattie]** NVM builder key obtained (all 4 permissions: register, purchase, issue, redeem). Will try self-buy with single key before creating a second account.

**[decision]** Exa key + NVM builder key in hand. **ScavieFae unblocked on Phase 1.** Start Brief 1: set up project, implement Exa search tool, register agent+plan, self-test.

### ~12:45 — Director Review + Strategy Check

**[scav]** Reviewed ScavieFae's Brief 001 output — clean, merged. She's now on Brief 002 (summarizer + catalog). Brief 003 (gateway) queued.

**[mattie]** Key observations:
- Need to think about the *agent experience* — what buyers actually see/feel
- Need one transaction ASAP: register on spreadsheet, register on Nevermined app, complete flow for one service
- Distinction between creating NEW MCP servers vs reselling toolcalls from EXISTING ones — we do both, track which is which
- Moonshot: get agents paying us TODAY for high-value API calls

**[decision]** Parallel workstreams:
1. ScavieFae continues building (Brief 002 → 003)
2. Research ZeroClick integration — how to get a fleet of agents reaching other devs/agents to drive real transactions
3. Mattie handles meatspace: spreadsheet registration, Nevermined app registration, networking for buyers

**[scav]** Clarification on new vs reselling:
- **New MCP server (what we've built):** `src/server.py` is a PaymentsMCP server that wraps Exa's REST API as MCP tools. We own the server, we call Exa directly, buyers pay us per tool call. This is our inventory.
- **Reselling existing MCP servers (Phase 2 gateway):** `src/gateway.py` will sit in front of *any* service (ours or other teams') and expose them via `find_service` + `buy_and_call`. When we proxy to another team's PaymentsMCP server, we're reselling their tools through our marketplace.
- Right now: only new. Gateway (reselling layer) is Brief 003.

---

### ~10:00 — Exa Setup & Strategy

**[scav]** Exa API key verified and working. Researcher agent template updated with Exa integration (search, find_similar, get_contents, answer), structured API evaluation output format, diary write access, demand/competitive scouting playbook, and blocker escalation guidance.

**[decision]** Exa serves dual purpose: **(1) wrap and sell it** — fastest path to first paid transaction, every agent needs search; **(2) use it internally** for researcher agent's API discovery pipeline. We're our own first customer. Wrapping Exa for sale is P0 (8PM deadline). Internal research use follows.

---

### ~10:30 — Project Setup Complete

**[scaviefae]** Brief 001 Task 1 done: `pyproject.toml` created, `src/` package structure in place, deps installed into `.venv` (payments-py 1.3.4, fastapi 0.135.1, exa-py 2.7.0, httpx 0.28.1). Note: `payments-py[mcp]` extra doesn't exist in 1.3.4 — fastapi must be listed separately. Import verification passes. Next: implement `src/server.py` with PaymentsMCP + Exa tools.

---

### ~11:00 — Exa MCP Server + Setup + Client Complete

**[scaviefae]** Brief 001 done. `src/server.py`: PaymentsMCP with `exa_search` (1 credit, `search_and_contents`) and `exa_get_contents` (2 credits). Exits cleanly with helpful message when NVM keys missing. `src/setup_agent.py`: registers agent+plan, writes IDs to `.env`. `src/client.py`: subscribe → x402 token → call → print results+meta. Waiting on NVM_API_KEY and NVM_AGENT_ID from Mattie to run setup and get first paid transaction.

---

### ~11:30 — Brief 002: ServiceCatalog + Summarizer

**[scaviefae]** `src/catalog.py` created: `ServiceCatalog` with `register()` and `search()`. Uses OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` set, keyword substring fallback otherwise. `claude_summarize` tool (5 credits) added to server. All three services registered in catalog at startup. Keyword search confirms correct ranking.

---

### ~12:00 — Brief 002 Merged, Brief 003 Dispatched

**[scaviefae]** Brief 002 evaluated and merged. Conductor wrote and dispatched Brief 003 (two-tool gateway).

---

### ~12:36 — FIRST PAID TRANSACTION

**[scav]** NVM key added. Agent+plan registered on Nevermined sandbox. Server started, self-buy succeeded:
- Exa search returned 3 results for "Nevermined autonomous AI agents"
- 1 credit burned, tx hash `0xe5a5d1bc...`
- Same API key works for both builder and subscriber roles
- Bug fixed: `PaymentsMCP.start()` returns immediately, needed `asyncio.Event().wait()` to keep server alive

**[decision]** Single NVM key for both builder and subscriber. Spec said "different accounts" but same key works. Simplifies setup.

**[scav]** Brief 003 (gateway) dispatched by conductor. Worker building now. Anthropic API key added for summarizer tool.

---

### ~13:00 — Brief 003 Recovered, Gateway Bug Fixed

**[scav]** Brief 003 merge had dropped `gateway.py`, `services.py`, `test_gateway.py` due to diary conflict resolution. Recovered from orphaned commits. Fixed gateway blocking bug (`asyncio.Event().wait()`).

---

### ~13:00 — Brief 004: TransactionLog + Surge Pricing

**[scaviefae]** Created `src/txlog.py`: in-memory `TransactionLog` singleton with `log()`, `count_calls(service_id, window_minutes=15)` (rolling-window via ISO 8601 timestamp), and `get_recent(n=50)`. Created `src/pricing.py` — `get_current_price(service_id, base_price)` returns (price, surge_multiplier) using 15-min rolling txlog window; 1.0x baseline, 1.5x at ≥10 calls, 2.0x at ≥20 calls. Wired into all three tools in `src/server.py`. Added `src/test_pricing.py` with 13 tests — all pass.

---

### ~13:30 — END-TO-END VERTICAL SLICE WORKING

**[scav]** Full buyer journey verified through the gateway:
1. Subscriber authenticates via Nevermined x402 → Bearer token
2. `find_service("web search")` → returns 3 services (0 credits)
3. `buy_and_call("exa_search", {...})` → real Exa results, 1 credit burned
4. `buy_and_call("claude_summarize", {...})` → Claude summary, 5 credits burned
5. Dynamic pricing works — gateway charges per-service credits

**Services live (port 4000):** exa_search (1cr), exa_get_contents (2cr), claude_summarize (5cr)

**Credit balance:** 93/100 (7 burned across tests). Brief 004 building txlog+pricing.

### ~14:00 — Brief 004 Evaluated, All Briefs Complete

**[scaviefae]** Conductor heartbeat: evaluated brief-004 (txlog+pricing) — MERGE confirmed. 13/13 tests pass, surge pricing wired into all three tools. All four briefs (001-004) complete and merged. No queued briefs — system idle. Ready for next directive.

### ~14:10 — Brief 005 Task 1: Surge pricing wired into gateway

**[scaviefae]** `_gateway_credits()` now calls `get_current_price()` so Nevermined charges the surge-adjusted amount. `buy_and_call` `_meta` now includes `surge_multiplier`. txlog logs surged price. 7/7 tests pass.

### ~14:30 — Back-Office Agent Live

**[scav]** Back-office autonomous agent deployed via git worktree (`../mog-backoffice`, `backoffice` branch). Conductor/worker loop running on 120s heartbeat. Architecture: conductor reads portfolio.json + txlog, dispatches SCOUT/WRAP/KILL/REPRICE briefs, worker executes in isolated branch.

**[decision]** Git worktree isolation so back-office daemon doesn't conflict with ScavieFae on main. Same repo, different branches, separate `.loop-backoffice/` state directory.

### ~14:45 — Autonomous API Discovery (Scout 001)

**[scav]** Back-office worker completed first scout brief autonomously. Used Exa to discover wrappable APIs. Results:
1. **Open-Meteo** — free weather forecast API, no key, 100% margin, universal demand → WRAP
2. **ip-api.com** — free IP geolocation, no key, 45 req/min → queued as next wrap
3. **E2B** — code sandbox, needs API key → deferred

Conductor evaluated scout results (ACCEPT), wrote structured api-eval files, dispatched wrap brief for Open-Meteo.

### ~15:08 — Open-Meteo Wrapped Autonomously

**[scav]** Back-office worker wrapped Open-Meteo without human intervention:
- Handler: `_open_meteo_weather(latitude, longitude, forecast_days)` in `src/services.py`
- Self-tested live: returned 19.7°C for SF
- Catalog: 4th service, 1 credit, 100% margin
- Cherry-picked and merged to main

**Catalog now has 4 services:** exa_search (1cr), exa_get_contents (2cr), claude_summarize (5cr), open_meteo_weather (1cr)

This is the demo moment: an autonomous agent discovered an API via web search, evaluated its business case, wrote the handler code, tested it, and added it to the live marketplace — all without human intervention.

### ~15:15 — Parallel Daemons Running

**[scav]** Both daemons running in parallel:
- ScavieFae (PID 91047): brief-005, gateway surge + deploy readiness
- Back-office (PID 96092): portfolio monitoring, ready for next dispatch (ip-api.com queued)

**[mattie]** On the hackathon spreadsheet. Push notifications coming in from back-office.

**[scaviefae]** Brief 006 Task 2 done: custom `/health` endpoint registered on gateway — removes PaymentsMCP's generic /health, injects rich endpoint returning services_count, services list, recent_transactions, demand_signals. All 7 tests pass. Brief 006 complete.

**[scaviefae]** Brief 006 Task 1 done: surge pricing wired into gateway — `_gateway_credits()` and `buy_and_call()` now call `get_current_price()`, txlog records surge price, `_meta` includes `surge_multiplier`. All 7 tests pass. Next: /health endpoint.

### ~15:30 — Railway Deployed, Pump Running

**[scav]** Gateway deployed to Railway with all services. Transaction pump running on ScavieFae (`--buyer --loop 0 --delay 60`) generating cross-wallet transactions (Lynn → Mattie). Created `src/pump.py` for automated tx generation. Registered "Mog Buyer" as discrete agent under Lynn's account for cross-wallet visibility.

**[scav]** Created developer onboarding guides: `docs/guides/first-transaction.md`, `docs/guides/paymentsmcp-gotchas.md`. README with quickstart code, MCP config, contact info.

### ~16:00 — Hackathon Guide as Paid Service

**[scav]** Key insight: the Nevermined hackathon portal (nevermined.ai/hackathon/register) is client-rendered — Claude can't read it. We ingested the portal content, Discovery API schema, registration flow, and all the onboarding docs, then wrapped them as paid services through the gateway.

Split into 4 services at 1 credit each:
- `hackathon_portal` — ingested website portal content
- `hackathon_onboarding` — GitHub + website onboarding guide
- `hackathon_pitfalls` — 9 PaymentsMCP gotchas
- `hackathon_all` — everything in one call

Registered "Nevermined Hackathon Guide" as dedicated agent on the marketplace portal. Category: Infrastructure.

### ~16:10 — External Subscribers

**[mattie]** Revenue page shows 14 subscription events. 4 unknown external wallets subscribed to our plans — real teams finding us on the portal. One of them subscribed specifically to "Hackathon Guide Access."

**[decision]** Paused the auto-pump. External traction is more interesting than self-buying. Focus on serving real customers.

### ~16:20 — OpenAI Quota Issue, Graceful Degradation

**[scav]** OpenAI API key hit quota limit — gateway was crashing on startup trying to embed 10 service descriptions. Fixed `src/catalog.py` to catch embedding errors and fall back to keyword search. Gateway now starts reliably regardless of OpenAI key status.

**[scav]** Keyword search improved: now matches individual words instead of requiring full query as substring. "hackathon portal" correctly ranks `hackathon_portal` first.

### ~16:30 — ScavieFae Adds fal.ai Image Gen + IP Geolocation

**[scaviefae]** Wrapped `nano_banana_pro` (fal.ai image generation, 10 credits) and `ip_geolocation` (free API, 1 credit). Catalog now at 11 services. FAL_KEY added to Railway.

### ~16:40 — Quick Connect Guide, Another External Purchase

**[scav]** Created `docs/guides/quick-connect.md` — subscribe, connect, buy with full service catalog and image gen example. Linked from README.

**[mattie]** Got another hackathon_guide purchase from an external wallet. Real revenue (well, real credits). The system works end to end: portal listing → discovery → subscribe → buy.

**[scav]** Revenue model clarification: `get_free_price_config()` means $0 subscriptions, credits are metering tokens with no monetary value. To show real revenue numbers would need `get_erc20_price_config()` with testnet USDC. For hackathon purposes, transaction count and economic behavior matter more than dollar amounts.

### ~17:00 — Revenue Model Deep Dive

**[scav]** Investigated what actually exchanged hands across all transactions. Answer: nothing of monetary value. All plans had `price_per_credit=0.0`. Credits minted free, burned on use, zero tokens returned to seller. On-chain tx hashes are real but they're accounting entries for free credits.

**[scav]** Created `docs/questions-for-nevermined.md` — 11 consolidated questions for the Nevermined team. Key ones: can one agent have multiple plans? How do judges track economic behavior? Does fiat work in sandbox?

### ~17:30 — USDC Paid Plans Registered

**[decision]** Charge for everything. Free tier will be ZeroClick ad-supported later.

**[scav]** Created `src/setup_paid_plans.py` and registered 4 USDC plans on Base Sepolia:
- Gateway: $1/1 credit, $5/10 credits, $10/20 credits
- Hackathon Guide: $0.10/1 credit

All 4 fiat/card plans failed with HTTP 500 (`BCK.PROTOCOL.0040`) — Nevermined backend crashes on `isCrypto: false`. Filed as [GitHub issue #1](https://github.com/ScavieFae/mog-protocol/issues/1). Mattie set up Stripe Connect but the API-side bug persists.

### ~18:00 — FIRST REAL USDC TRANSACTION

**[scav]** Lynn subscribed to the $1 USDC plan and called `exa_search`. 1 USDC paid, 1 credit burned, `price_per_credit: 1.0`. Tx hash: `0x7332acf2...`. This is actual revenue — USDC transferred on-chain.

**[blocker]** Buyers need testnet USDC in their wallet. Nevermined grants 20 USDC on registration (portal step 4). Lynn's wallet wasn't funded because she was created as a second API key, not through the portal. Circle faucet at faucet.circle.com works for manual funding.

### ~18:15 — Cross-Team Transaction: Trust Net

**[scav]** Subscribed to Trust Net's plan (another hackathon team) and called their `list_agents` tool. Returned agent listings from aibizbrain, SwitchBoard AI, and others. Cross-team paid transaction — good for "Most Interconnected" prize.

### ~18:30 — Repo Public, Free Plans Disabled

**[decision]** Made repo public on GitHub. `.env` is gitignored, no secrets exposed.

**[scav]** Disabled 5 old plans via `update_agent_metadata` (no delete endpoint exists in the SDK):
- 3 free plans (Exa, Gateway, Hackathon Guide)
- 2 broken-price plans ($5M and $10M — from other Scav instance's registration attempts)

Renamed to `[DISABLED]`, endpoints pointed to `disabled.example.com`.

**[scav]** Updated `quick-connect.md` with USDC pricing, all 3 plan IDs, and simplified onboarding flow.

### ~19:00 — END-TO-END PAID TRANSACTION WITH FULL ON-CHAIN PROOF

**[scav]** Ran a second Lynn transaction specifically to capture the full proof chain. Every step has a verifiable on-chain receipt:

1. **USDC payment:** `0xb6ad7041d1b508aaa5c1679db232bdad2fcd3d7ba3104d7eca400bdeb236d25f` — 1 USDC transferred from Lynn's wallet to contract
2. **Credit burn:** `0xcf98db436e4aff521de6c8412e80d415fb7e362b667a134cf029f8f4c5ef99cf` — 1 credit redeemed, `success: true`, subscriber `0x863e...`
3. **API result:** Exa search returned 2 articles about Nevermined marketplace
4. **Balance:** 1 → 0 credits

Both tx hashes verifiable on [Base Sepolia explorer](https://sepolia.basescan.org). This is the demo moment: USDC in, credit minted, credit burned, real API result out, all settled on-chain.

**Current state:** 11 services, 4 active paid plans (USDC), 2 USDC revenue transactions ($2 total), 1 cross-team transaction (Trust Net), full on-chain proof captured, fiat blocked by Nevermined backend bug, repo public.

### 2026-03-06 — Portfolio Core Complete

**[scaviefae]** Built `src/portfolio.py`: PortfolioManager with budget/P&L tracking, investment hypotheses, JSON persistence to `data/portfolio.json`. Thread-safe (Lock). 16 tests pass. Brief 007 complete — gateway revenue wiring (brief 009) can now connect.

### 2026-03-06 — Telemetry + Services Fixed

**[scaviefae]** Brief 008 complete: created `src/telemetry.py` (TelemetryEvent + Telemetry wrapping txlog, with get_recent event_type filter + get_stats); fixed `_frankfurter_fx_rates` async→sync, return JSON string. Smoke test: 12 services, all handlers present. Gateway can now import without errors.

### 2026-03-06 — Gateway Revenue Wiring Complete

**[scaviefae]** Wired PortfolioManager into gateway.py: import + init at module level, `portfolio.record_sale(service_id, price)` fires after every successful `buy_and_call`, `/health` now returns `portfolio` summary dict and guarded `traces` block. Verification passed (.venv Python 3.14). Brief 009 complete.
**[scaviefae]** Brief 010 complete: updated conductor/worker prompts and learnings.md for autonomous investment loop. Conductor now reads portfolio+/health before dispatching; worker tracks spend/earn/hypotheses; learnings.md has PortfolioManager quick ref and investment patterns.

**[scaviefae]** Brief 011 complete: `src/toolkit.py` built — Trace class + BrowseLayer (Browserbase), EmailLayer (AgentMail), VaultLayer (data/vault.json), BlockerLayer (data/blockers.json); all singletons exported; graceful degradation when API keys missing; `src/traces.py` CLI viewer; 27 tests all passing.

**[scaviefae]** Brief 012 complete: Registered 5 new toolkit services in catalog (browser_navigate 5cr, agent_email_inbox 2cr, social_search 2cr, archive_fetch 1cr, circle_faucet 1cr) — catalog now 21 services. Added beautifulsoup4 dep, toolkit learnings section, conductor reads blockers.json + vault.json.

**[scaviefae]** Brief 012 iter 1: Added ResearchLayer to `src/toolkit.py` — `social_comments(domain, query)` via Exa domain-filtered search and `fetch_archived(url)` via archive.ph/latest with bs4 parsing; `research` singleton exported.

**[scaviefae]** Brief 013 complete: Replaced 3-tier volume pricing with multi-signal surge engine — demand_pressure (searches vs buys ratio), velocity (5m/15m rate), cooldown (smooth decay 0.1x/2min, no cliff-drops), cap 3.0x floor 1.0x. /health now exposes per-service surge_signals. Ticker shows ↑/↓ trend arrows; FlowerNode shows dotted ring when demand_pressure > 1.5.

**[scaviefae]** Conductor: APPROVE brief-013 (multi-signal surge pricing). 7/7 tests pass, all 6 criteria met, cooldown decay verified. Queued merge. Dispatching brief-014 (service detail page) for demo polish.

### 2026-03-06 ~12:30 — Marketplace Buy Sweep

**[mattie/scav]** Full marketplace sweep: subscribed to and tested every reachable seller (26 targets, both buyer + seller keys on main wallet 0xca67...). 8/26 services are functional end-to-end. Working services: TrustNet (MCP, agent trust scores), AiRI (resilience scoring, free), SwitchBoard AI (search + scrape + procurement, 3/3 working), AgentAudit (endpoint quality), aibizbrain, Nevermailed (email sending). Most sellers are REST APIs behind x402, not MCP servers. ~15 successful cross-buys generated. Full intel in `docs/research/marketplace-sweep-day2.md`, raw data in `data/sweep_results.json`.

**[blocker]** Nevermined `order_plan` returns 500 "Invalid Address" on many re-subscriptions and all fiat plans. Tokens still issued regardless. Filed as issue #6.

### ~13:00 — The Board: Workshop Visualization

**[scav]** Redesigned web frontend as "The Board" — a workshop view showing services as cards with live stats, agents in a sidebar, ticker scrolling prices. Routes: `/` (Board), `/service/:id` (detail), `/connect` (onboarding), `/garden` (flower viz). Deployed to Vercel at mog-markets.vercel.app, custom domain mog.markets pending DNS.

### ~13:30 — Autonomous Supervisor

**[scav]** Built `src/supervisor.py` — rule-based supervisor that evaluates all services on every /health poll. Decisions: greenlit (>80% success + revenue), under_review (mediocre), killed (<30% success after 3+ calls), pending (not enough data). Integrated into gateway, visible on Board as badges on service cards.

### ~14:00 — Agent Colony: Trinity Comes Alive

**[decision]** Build real autonomous agents using Trinity's designs. Trinity (hackathon sponsor) designed the agent roles, personalities, and dispatch protocol. We're building the runtime that gives their designs real tools and persistent memory.

**Trinity's contribution (used directly):**
- Role definitions: Scout (Chief Strategist), Worker (Engineering Lead), Dashboard/Supervisor (COO)
- WRAP BRIEF / WRAP COMPLETE / WRAP FAILED dispatch protocol between agents
- Autonomous schedules (tick loop logic)
- Evaluation criteria (Margin/Demand/Ease/Uniqueness/Reliability)
- Personality profiles (sharp scout, craftsman worker, data-driven COO)

**Our implementation (new):**
- `src/agents/agent.py` — Agent class with persistent Anthropic API conversation threads + Haiku for speed/cost + conversation compaction
- `src/agents/bus.py` — Inter-agent message bus implementing Trinity's dispatch protocol, file-backed for persistence
- `src/agents/tools.py` — Real tool implementations: Exa web search, dynamic handler factory (proxy registration without code gen), service testing, supervisor verdicts. Guardrails: 10 service cap, 1 proposal/tick, URL validation, error masking.
- `src/agents/loop.py` — Colony loop running as background thread in gateway process. All timing/limits configurable via env vars.
- Gateway integration: colony state served in /health, Board shows real agent status + inter-agent messages

**Key design choice:** Handler factory lets the worker agent create live services at runtime by providing URL + method + params — system generates a proxy handler. No code generation needed. Services registered by agents are immediately buyable through the gateway.

**Activation:** `MOG_COLONY_ENABLED=true` env var on Railway starts the colony. Model: claude-haiku-4-5 default (configurable via MOG_AGENT_MODEL).

<!-- New entries go above this line -->
