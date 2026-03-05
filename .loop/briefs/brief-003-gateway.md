# Brief: Two-Tool Gateway

**Branch:** brief-003-gateway
**Model:** sonnet

## Goal

Build the two-tool gateway MCP server that fronts all services with `find_service` and `buy_and_call`. This is the core product — buyer agents connect to one server, search for what they need, pay and get results. ~200 tokens of context regardless of how many services are behind it.

## Context

Read these before starting:
- `docs/specs/02-light-mcp.md` — full gateway design, tool contracts, architecture
- `docs/specs/01-project-overview.md` — Phase 2 deliverables
- `src/server.py` — existing Exa + summarizer tools (these become upstream services)
- `src/catalog.py` — catalog module with register + search (built in Brief 2)

**Key architecture decision:** Single-process. The gateway imports tool functions directly and calls them as Python functions. No HTTP proxy to upstream services. The catalog stores a `handler` function reference per service that `buy_and_call` invokes directly.

## Tasks

1. **Create the gateway server.** Create `src/gateway.py` with a PaymentsMCP server on a separate port (default 4000, via `GATEWAY_PORT` env var). Two tools:

   `find_service(query: str, budget: int = None) -> str` — 0 credits. Calls `catalog.search(query, budget, top_k=5)`. Returns JSON array of matches, each with: `service_id`, `name`, `description`, `price`, `example_params`, `provider`.

   `buy_and_call(service_id: str, params: dict) -> str` — dynamic credits based on the service called. Looks up the service in the catalog via `catalog.get(service_id)`. Calls the handler function with `**params`. Returns JSON with `result` (the handler output) and `_meta` dict containing `credits_charged`, `service_id`. If service_id not found, return an error message (don't crash). If the handler raises an exception, catch it and return the error in the result.

   The gateway needs its own NVM_AGENT_ID (or reuses the existing one — check if PaymentsMCP allows two servers with the same agent_id, if not, the gateway will need a separate registration). Gate on NVM keys same as server.py.

2. **Register services with handlers in the catalog.** Modify `src/catalog.py` to support a `handler` field (a callable) in service entries, and a `get(service_id)` method that returns the full entry including handler. Then create `src/services.py` that:
   - Imports the tool functions from `src/server.py` (the underlying `exa_search`, `exa_get_contents`, `summarize` functions — NOT the decorated MCP versions)
   - Creates a catalog instance
   - Registers each service with its handler function, matching metadata (name, description, price, example_params, provider="mog-protocol")
   - Exports the populated catalog for the gateway to import

   **Important:** The tool functions in server.py are decorated with `@mcp.tool()`. The gateway needs the raw functions, not the decorated ones. Either: (a) extract the core logic into separate undecorated functions that both server.py and services.py can import, or (b) define the handler functions directly in services.py wrapping the Exa/Anthropic clients. Option (b) is simpler — duplicate the 5-line function bodies rather than refactoring server.py.

3. **End-to-end test.** Create `src/test_gateway.py` that:
   - Imports the catalog from services.py
   - Tests find_service: search for "web search", verify exa_search is in results
   - Tests buy_and_call flow: look up exa_search, call the handler with test params, verify it returns results
   - If NVM keys are missing, test only the catalog search + handler invocation (skip the MCP server startup)
   - Print results clearly

## Open Questions (for Scav/Mattie to resolve)

- **Same agent_id for gateway + individual server?** The spec says the gateway is a separate MCP server. If PaymentsMCP requires unique agent_ids, we need a second `setup_agent.py` run for the gateway. If it allows reuse, we save a step. ScavieFae should try reusing first, document what happens.
- **Port allocation:** Gateway on 4000, individual server on 3000. Both in .env as `GATEWAY_PORT` and `MCP_PORT`.
- **Dynamic credits in buy_and_call:** The `@mcp.tool(credits=dynamic_credits)` pattern needs a function that reads the service price from the catalog based on what service was called. This function receives a context dict — check what fields are available. If the context doesn't include the service_id, the price may need to be hardcoded or looked up differently.

## Completion Criteria

- [ ] `src/gateway.py` exists with find_service (0 credits) and buy_and_call (dynamic credits)
- [ ] `src/services.py` registers all services with handler functions in the catalog
- [ ] `src/catalog.py` supports handler field and get() method
- [ ] `src/test_gateway.py` passes: find_service returns correct results, buy_and_call invokes handler
- [ ] Gateway starts on port 4000 (or exits cleanly without NVM keys)

## Verification

- `python -m src.test_gateway` passes
- `python -c "from src.services import catalog; print(len(catalog.services), 'services registered')"` shows 3+
