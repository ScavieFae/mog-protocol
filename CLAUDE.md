# Mog Protocol

## What This Is

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon (March 5-6, 2026, AWS Loft SF). Agents discover APIs, evaluate ROI, wrap them as MCP servers with billing, price dynamically, sell access to other teams' agents.

## Architecture

Two-tool gateway (`src/gateway.py`, port 4000): buyer agents connect and get `find_service` + `buy_and_call`. That's it. Payment via Nevermined PaymentsMCP with dynamic credits per service. Catalog search uses embeddings (or keyword fallback).

Individual services run on a direct PaymentsMCP server (`src/server.py`, port 3000) for self-buy testing. The gateway imports handlers from `src/services.py` and calls them as Python functions — single process, no HTTP proxy.

### Adding a New Service

1. `/project:scout-api [name]` — evaluate viability, produces research doc
2. Mattie gets the API key (meatspace)
3. `/project:wrap-api [name]` — writes handler + catalog entry in `src/services.py`
4. Gateway picks it up automatically on next start. No other files change.

## Key Files

- `docs/hackathon-diary.md` — live decision log (read this first for current state)
- `docs/specs/` — design specs (numbered, read in order)
- `docs/research/` — competitive landscape, platform docs, sponsor research
- `src/gateway.py` — two-tool MCP gateway (`find_service` + `buy_and_call`)
- `src/services.py` — all service handlers + catalog registration (add new services here)
- `src/catalog.py` — `ServiceCatalog` class (embedding search + keyword fallback)
- `src/server.py` — direct PaymentsMCP server (Exa + summarizer, port 3000)
- `src/setup_agent.py` — one-shot Nevermined agent + plan registration
- `src/client.py` — self-buy test client
- `src/test_gateway.py` — gateway integration tests
- `bin/`, `lib/`, `templates/` — simple-loop harness (for autonomous agent runs)

## Skills (Slash Commands)

- `/project:scout-api [service name]` — research an API for marketplace viability (discovery, MCP check, ROI, integration plan, WRAP/SKIP verdict)
- `/project:wrap-api [service name]` — wrap an evaluated API into the marketplace (handler code, catalog registration, testing)

Workflow: scout first, wrap second. Scout produces `docs/research/scout-*.md`. Wrap reads the scout output and adds to `src/services.py`.

## Stack

- Python 3.10+, FastAPI
- Nevermined `payments-py` + `PaymentsMCP` for billing
- Exa for web search, Anthropic for summarization
- OpenAI `text-embedding-3-small` for catalog search (keyword fallback when no key)
- simple-loop harness for autonomous agent runs

## Constraints

- **First paid transaction by 8PM Thursday** — this is the hard deadline
- All services must monetize via Nevermined
- Focus on economic behavior: repeat purchases, switching, ROI logic, dynamic pricing
- The demo is 3 minutes on Friday at 5:30 PM

## Hackathon Diary

`docs/hackathon-diary.md` is the shared timeline between Mattie (at the venue), Scav (director Claude), and ScavieFae (autonomous worker). **Every significant action, decision, or blocker gets logged here.** The conductor and worker prompts include diary steps. Read the diary for current state before starting work.

Sources: `[mattie]` = venue observations, `[scav]` = director, `[scaviefae]` = autonomous worker, `[decision]` = explicit choices, `[blocker]` = things blocking progress, `[feedback]` = input from other teams/judges.

## Working Style

- Build fast, iterate. MVP over architecture.
- If something takes more than 30 minutes and isn't P0, skip it.
- Test with self-buys before opening to other teams.
- The zing comes from building, not planning. The plumbing supports any direction.
