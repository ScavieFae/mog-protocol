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

<!-- New entries go above this line -->
