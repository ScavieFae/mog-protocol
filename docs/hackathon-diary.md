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

### ~23:45 — IP Geolocation Wrapped

**[backoffice]** Evaluated and merged backoffice-003-wrap-ip-api. Worker added `_ip_geolocation` handler (ip-api.com, free, no key). Clean code, proper error handling, catalog registered at 1 credit/call. Synced backoffice branch with main (resolved divergence from earlier open-meteo merge path).

**Catalog now has 7 services:** exa_search (1cr), exa_get_contents (2cr), claude_summarize (5cr), open_meteo_weather (1cr), ip_geolocation (1cr), hackathon_guide (1cr), hackathon_discover (1cr)

<!-- New entries go above this line -->
