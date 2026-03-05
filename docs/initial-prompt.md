# Mog Protocol — Initial Prompt

Use this when starting a new Claude Code session in the mog-protocol project.

---

## Context

You're building Mog Protocol — an autonomous API marketplace for the Nevermined hackathon happening RIGHT NOW (March 5-6, 2026). The concept is documented in `docs/concept.md`. Design specs are in `docs/specs/` (numbered, read in order). Research on the competitive landscape, sponsors, and orchestration patterns lives in `docs/research/`.

## The Product

A two-tool MCP gateway where buyer agents call `find_service(query, budget)` to discover APIs and `buy_and_call(service_id, params)` to pay and execute in one call. Payment is via Nevermined `@requires_payment`, embedded inside the gateway. Dynamic pricing responds to demand in real time.

## Priority Order

1. **Gateway server** — FastAPI + FastMCP serving `find_service` and `buy_and_call` (spec: `docs/specs/02-light-mcp.md`)
2. **Nevermined integration** — `@requires_payment` on all tools, x402 payment flow (spec: `docs/specs/06-nevermined-integration.md`)
3. **Manual service wrapping** — Wrap Exa search and one other API we have keys for
4. **Catalog index** — In-memory embeddings for `find_service` semantic search
5. **Dynamic pricing** — Three-tier surge pricing on 15-minute rolling window (spec: `docs/specs/03-dynamic-pricing.md`)
6. **Autonomous wrapper agent** — simple-loop brief for discovering and wrapping APIs (spec: `docs/specs/04-wrapper-agent.md`)
7. **Marketplace feed** — WebSocket live feed for demo (spec: `docs/specs/05-marketplace-feed.md`)

## Hard Deadline

First paid agent-to-agent transaction by 8PM Thursday. No transaction = no prize eligibility.

## What to Read First

1. `CLAUDE.md` — project overview and constraints
2. `docs/specs/01-project-overview.md` — architecture and components
3. `docs/specs/02-light-mcp.md` — the core gateway design
4. `docs/specs/06-nevermined-integration.md` — how payments work

Then start building the gateway server.
