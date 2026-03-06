# Brief: Finish Toolkit Services + Docs

**Branch:** brief-013-finish-toolkit-services
**Model:** sonnet

## Goal

Complete the remaining 4 tasks from brief-012 that never landed. ResearchLayer is already on main — this brief registers the sellable services, updates docs, and adds the dependency.

## Context

Read these before starting:
- `src/services.py` — where to register new services (check what's already there)
- `src/toolkit.py` — toolkit module with BrowseLayer, EmailLayer, VaultLayer, BlockerTracker, ResearchLayer
- `docs/specs/10-agent-toolkit.md` — full spec
- `.loop/knowledge/learnings.md` — add toolkit patterns here
- `.loop/prompts/conductor.md` — needs toolkit awareness

## Tasks

1. **Register 5 sellable services in `src/services.py`.**

   - `browser_navigate` (5 credits) — Browserbase session, navigate URL, return title+text. Params: `url`.
   - `agent_email_inbox` (2 credits) — Create disposable email via AgentMail. Returns inbox ID + address. Params: `label`.
   - `social_search` (2 credits) — Search social domain for posts/comments. Params: `domain`, `query`, `max_results` (optional, default 10).
   - `archive_fetch` (1 credit) — Fetch archived URL from archive.ph. Params: `url`.
   - `circle_faucet` (1 credit) — Claim 20 testnet USDC from Circle faucet via Browserbase. Params: `wallet_address`, `network` (optional, default "BASE"), `currency` (optional, default "USDC").

   Each handler wraps the corresponding toolkit method, returns JSON string, handles missing API keys gracefully (return error JSON, don't crash). All handlers must be sync (use `httpx.get()` not `aiohttp`).

2. **Update `.loop/knowledge/learnings.md` — add toolkit section.** Practical guidance:
   - List all available toolkit methods (browse, email, vault, blockers, research)
   - When blocked by signup: check vault first, try browse+email, file blocker if stuck
   - Blocker types and recommendations

3. **Update conductor prompt (`.loop/prompts/conductor.md`) with toolkit awareness.**
   - Read `data/blockers.json` for recent blockers during assessment
   - When blocker has recommendation=RETRY_WITH_TOOL, dispatch retry brief
   - When dispatching scout briefs, remind worker toolkit is available
   - Check `data/vault.json` for newly acquired keys

4. **Add `beautifulsoup4` to `pyproject.toml` dependencies.**

## Completion Criteria

- [ ] 5 new services registered in catalog
- [ ] All handlers sync, return JSON strings, handle missing keys
- [ ] learnings.md has toolkit section
- [ ] Conductor prompt references blockers.json and vault.json
- [ ] beautifulsoup4 in dependencies
- [ ] `python -c "from src.services import catalog; print(len(catalog.services))"` shows >= 17

## Verification

- `python -c "from src.services import catalog; print(f'{len(catalog.services)} services')"` >= 17
- Read conductor prompt and confirm it references blockers.json and vault.json
