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

### ~11:30 — Brief 002 Task 2: ServiceCatalog built

**[scaviefae]** `src/catalog.py` created: `ServiceCatalog` with `register()` and `search()`. Uses OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` set, keyword substring fallback otherwise. Import check passes. Next: register all three services in `server.py` and export catalog instance.

### ~11:45 — Brief 002 Complete: Catalog registered in server.py

**[scaviefae]** Brief 002 done. `src/server.py` now imports `ServiceCatalog`, instantiates it after `mcp` setup, and registers all three services: `exa_search` (1cr), `exa_get_contents` (2cr), `claude_summarize` (5cr). `catalog` exported at module level for gateway import. Keyword search test confirms `exa_search` ranks first for "web search" query. Brief 003 (two-tool gateway) is next.

<!-- New entries go above this line -->
