# Brief: Second Service + Catalog Index

**Branch:** brief-002-second-service-catalog
**Model:** sonnet

## Goal

Add a Claude summarizer tool as a second paid service alongside Exa search, and build a minimal catalog module that indexes services with embeddings for semantic search. This gives us two sellable tools and the foundation for the gateway's `find_service`.

## Context

Read these before starting:
- `docs/specs/04-wrapper-agent.md` — Brief 2 scope (second service + catalog)
- `docs/specs/02-light-mcp.md` — the gateway design (catalog feeds `find_service`)
- `src/server.py` — existing Exa MCP server (add the new tool here)

The Anthropic API key is available as `ANTHROPIC_API_KEY` in `.env`. Use the `anthropic` Python SDK.

## Tasks

1. **Add Claude summarizer tool to server.** In `src/server.py`: add a `claude_summarize` tool (5 credits) that takes `text: str` and `format: str = "bullets"` (options: "bullets", "paragraph", "structured"). Calls `anthropic.Anthropic().messages.create()` with claude-sonnet-4-20250514 to summarize the input text in the requested format. Keep it simple — one API call, return the summary text. Add `anthropic` to `pyproject.toml` dependencies.

2. **Build catalog module.** Create `src/catalog.py` with a `ServiceCatalog` class:
   - `register(service_id, name, description, price_credits, example_params, provider)` — stores service metadata
   - `search(query, budget=None, top_k=3)` — returns top matches by cosine similarity on description embeddings
   - Use `openai.OpenAI().embeddings.create(model="text-embedding-3-small")` for embeddings (OPENAI_API_KEY in .env)
   - Embeddings computed at registration time and cached in-memory
   - If OPENAI_API_KEY is not set, fall back to simple keyword matching (substring search on name+description)
   - Add `openai` to `pyproject.toml` dependencies

3. **Register services in catalog and test.** In `src/server.py`, after creating the PaymentsMCP instance, instantiate `ServiceCatalog` and register both tools:
   - `exa_search`: "Semantic web search. Returns relevant snippets with source URLs.", 1 credit, example_params=`{"query": "latest AI research", "max_results": 5}`
   - `exa_get_contents`: "Fetch full text content from URLs.", 2 credits, example_params=`{"urls": ["https://example.com"]}`
   - `claude_summarize`: "Summarize text using Claude. Supports bullets, paragraph, or structured format.", 5 credits, example_params=`{"text": "Long article text...", "format": "bullets"}`
   - Export the catalog instance so the gateway can import it later

## Completion Criteria

- [ ] `claude_summarize` tool added to server.py with @mcp.tool(credits=5)
- [ ] `src/catalog.py` exists with ServiceCatalog class, register + search methods
- [ ] Catalog uses embeddings when OPENAI_API_KEY is set, keyword fallback otherwise
- [ ] All three tools registered in catalog at server startup
- [ ] `python3 -c "from src.catalog import ServiceCatalog; print('catalog ok')"` passes

## Verification

- Import check: `python3 -c "import anthropic; from src.catalog import ServiceCatalog; print('ok')"`
- Catalog search: instantiate ServiceCatalog, register test services, search("web search") returns exa_search as top result
- Server still starts cleanly (with NVM keys) or exits with helpful message (without)
