# Mog Protocol

## What This Is

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon (March 5-6, 2026, AWS Loft SF). Agents discover APIs, evaluate ROI, wrap them as MCP servers with billing, price dynamically, sell access to other teams' agents.

## Architecture

Two-tool gateway: buyer agents connect and get `find_service` + `buy_and_call`. That's it. Payment via Nevermined `@requires_payment` is embedded inside `buy_and_call`. Catalog search uses embeddings over tool descriptions.

## Key Files

- `docs/concept.md` — full concept doc with zing directions
- `docs/specs/` — design specs (numbered, read in order)
- `docs/research/` — competitive landscape, platform docs, sponsor research
- `src/gateway/` — the two-tool MCP gateway server
- `src/wrapper/` — OpenAPI → MCP server generation pipeline
- `src/pricing/` — dynamic pricing engine
- `bin/`, `lib/`, `templates/` — simple-loop harness (for autonomous agent runs)

## Stack

- Python 3.10+, FastAPI, FastMCP
- Nevermined `payments-py` for billing
- Exa for API discovery, Apify for doc scraping
- OpenAI `text-embedding-3-small` for catalog search
- simple-loop harness for autonomous wrapper agent

## Constraints

- **First paid transaction by 8PM Thursday** — this is the hard deadline
- All services must monetize via Nevermined
- Focus on economic behavior: repeat purchases, switching, ROI logic, dynamic pricing
- The demo is 3 minutes on Friday at 5:30 PM

## Working Style

- Build fast, iterate. MVP over architecture.
- If something takes more than 30 minutes and isn't P0, skip it.
- Test with self-buys before opening to other teams.
- The zing comes from building, not planning. The plumbing supports any direction.
