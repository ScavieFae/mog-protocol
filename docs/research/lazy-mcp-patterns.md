# Lazy MCP — Patterns for Reducing Tool Context Bloat

[source: web research, March 4 2026]

---

## The Problem

MCP servers expose tool lists upfront. An agent connecting to a marketplace with 50+ tools gets slammed with descriptions, schemas, and parameter docs before it can do anything useful. At scale (hundreds of tools), this eats context windows and degrades model performance.

The MCP spec doesn't have native lazy loading. But several patterns have emerged.

---

## Pattern 1: OpenMCP Schema Lazy Loading

**How it works:** Server exposes tool *names* only (no schemas). Client calls `expandSchema` to get full details for specific tools on demand.

```
Initial load: ["search_web", "get_weather", "translate_text", ...]  # names only
Agent picks: expandSchema("search_web")
Server returns: { parameters: {...}, description: "...", examples: [...] }
```

**Token reduction:** ~90% on initial handshake.

**Trade-off:** Requires an extra round-trip per tool. Works well when the agent has good intuition about which tool name matches its need. Falls apart if names are opaque.

**Source:** OpenMCP project (community, not spec-native).

---

## Pattern 2: Gateway / Retrieval-First

**How it works:** A gateway sits in front of all MCP servers. Exposes exactly two tools:

1. `retrieve_tools(query)` — semantic search over available tools, returns top-k matches with full schemas
2. `call_tool(server, tool, params)` — proxy call to the actual MCP server

Agent never sees the full tool catalog. It describes what it needs, gets back the 3-5 most relevant tools, picks one.

**Token reduction:** ~50% overall, but the accuracy gain is the real win.

**Performance data:** One benchmark showed accuracy jumping from 13% to 43% on complex tool-selection tasks when using retrieval-first vs. full catalog.

**Trade-off:** Adds latency (retrieval step). Quality depends entirely on the embedding/search quality of the gateway. If the retrieval misses the right tool, the agent can't find it.

**This is closest to what we'd want for the hackathon marketplace** — buyer agents search for capabilities, not browse catalogs.

---

## Pattern 3: Dynamic Context Loading (3-Level Hierarchy)

**How it works:** Tools organized in a tree:

```
Level 0: Categories      ["data_apis", "ml_models", "utilities"]
Level 1: Tool groups     ["search_engines", "databases", "scrapers"]
Level 2: Individual tools  full schema for specific tool
```

Agent drills down through levels. Each level is a tool call.

**Trade-off:** More structured than retrieval-first but more rigid. Works for well-organized catalogs, breaks for organic/messy collections. Three round-trips before you can call anything.

---

## Pattern 4: Group Placeholder Loading

**How it works:** Tools are grouped by capability. Initial load shows one placeholder per group:

```
"web_search_tools" (5 tools available — expand to see options)
"data_processing_tools" (3 tools available)
```

Expanding a group loads all tools in that group.

**Trade-off:** Good middle ground. Agent sees the landscape without the full weight. But grouping quality matters — bad groups mean bad discovery.

**Status:** Proposed for Claude Code but not shipped as of March 2026.

---

## MCP Spec Status

The spec itself has:
- `listChanged` notifications — server can tell clients when tool list updates
- Pagination on `tools/list` — clients can page through large catalogs
- **No native lazy loading, retrieval, or hierarchical discovery**

These patterns are all community/application-layer solutions built on top of the spec.

---

## Relevance to Hackathon

If our marketplace grows beyond ~10 tools, buyer agents will struggle. Pattern 2 (gateway/retrieval-first) is the most practical for our case:

- We control the gateway (it's our marketplace)
- Buyer agents only need two tools: "what's available?" and "buy it"
- Semantic search over tool descriptions handles discovery
- Keeps buyer agent context lean regardless of catalog size

This also maps to the "Craigslist" metaphor — buyers search for what they need, they don't browse every listing.
