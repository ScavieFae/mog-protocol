# Brief: Phase 1 Seller — Exa Search MCP Service

**Branch:** brief-001-phase1-seller
**Model:** sonnet

## Goal

Get the first paid MCP service running on Nevermined. Fork the mcp-server-agent pattern, implement Exa search as a paid tool, register with Nevermined, and verify the full payment flow with a self-buy.

## Context

Read these before starting:
- `docs/specs/04-wrapper-agent.md` — Brief 1 scope and Exa tool code
- `docs/specs/06-nevermined-integration.md` — Nevermined SDK patterns, PaymentsMCP, setup, client flow
- `docs/research/hackathon-repo.md` — reference implementation teardown
- `docs/specs/01-project-overview.md` — overall architecture

Reference repo: `nevermined-io/hackathons/agents/mcp-server-agent/` (don't clone, use the patterns from our specs and research docs).

## Tasks

1. **Project setup.** Create `pyproject.toml` with dependencies: `payments-py[mcp]`, `exa-py`, `python-dotenv`, `httpx`. Create `src/` package structure: `src/__init__.py`, `src/server.py`, `src/setup_agent.py`, `src/client.py`. Load env vars from `.env` (EXA_API_KEY is already there; NVM_API_KEY, NVM_AGENT_ID, NVM_PLAN_ID, NVM_SUBSCRIBER_API_KEY will be added by Mattie). Install deps into the project venv at `.venv/`.

2. **Implement the Exa search MCP server.** In `src/server.py`: initialize `Payments` and `PaymentsMCP`, implement `exa_search` tool (1 credit) using `exa_py.Exa`. The tool takes `query: str` and `max_results: int = 5`, calls `exa.search()`, returns JSON with title/url/snippet for each result. Add a second tool — `exa_get_contents` (2 credits) that takes a list of URLs and returns their full text content via `exa.get_contents()`. Server starts with `mcp.start(port=3000)`. Gate on NVM_API_KEY and NVM_AGENT_ID being set — if missing, print a clear message saying "Waiting for Nevermined API keys. Set NVM_API_KEY and NVM_AGENT_ID in .env" and exit cleanly.

3. **Implement setup and client scripts.** `src/setup_agent.py`: registers agent + plan with Nevermined using `register_agent_and_plan()`, prints the agent_id and plan_id, appends them to `.env`. Use `get_free_price_config()` and `get_dynamic_credits_config(credits_granted=100, min_credits_per_request=1, max_credits_per_request=10)`. MCP endpoints: `mcp://mog-exa/tools/exa_search` and `mcp://mog-exa/tools/exa_get_contents`. `src/client.py`: subscribes to plan, gets x402 token, calls `exa_search` with a test query, prints result and credits info.

## Completion Criteria

- [ ] `pyproject.toml` exists with correct deps
- [ ] `src/server.py` runs and exposes two Exa tools via PaymentsMCP
- [ ] `src/setup_agent.py` registers agent+plan (requires NVM_API_KEY)
- [ ] `src/client.py` does a full self-buy flow (requires NVM_SUBSCRIBER_API_KEY)
- [ ] Server prints clear "waiting for keys" message if NVM env vars are missing

## Verification

- `python3 -c "import payments_py; import exa_py; print('deps ok')"` passes (run from .venv)
- Server starts without error when NVM keys are set
- Server exits cleanly with helpful message when NVM keys are missing
