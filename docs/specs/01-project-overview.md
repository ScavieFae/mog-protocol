# Mog Protocol — Project Overview

**Classification: NECESSARY**

## What This Is

An autonomous agent marketplace that wraps APIs as paid MCP tools, prices them dynamically, and sells access to other agents — all via Nevermined payment rails. Buyer agents connect to one MCP server, get two tools, search for what they need, pay and get results.

## Core Thesis

API providers ship 600 endpoints. Agents need 12. We sit at the transaction layer, see demand in real time, and become a better packager of their API than they are. The marketplace scales; the buyer agent's context stays two tools wide.

## Architecture

Two layers: individual paid services, and a gateway that fronts them all.

```
Buyer Agent
    | MCP (Streamable HTTP, 2 tools always)
    v
Mog Gateway
    find_service(query, budget) -> matches with prices
    buy_and_call(service_id, params) -> result + cost
    [PaymentsMCP handles x402 auth]
    |
    +---> Catalog Index (in-memory embeddings, numpy)
    +---> Pricing Engine (surge tiers, demand tracking)
    +---> Transaction Log (feeds pricing + demo feed)
    |
    v
Individual Services (behind the gateway)
    - Exa search wrapper (PaymentsMCP)
    - Other wrapped APIs
    - Other teams' services (proxied)
```

## Build Phases

### Phase 1: First Transaction (Thursday, by 8PM)

Fork `nevermined-io/hackathons/agents/mcp-server-agent/`. Swap DuckDuckGo for Exa. Register with Nevermined. Get a self-buy working, then open to other teams.

**Deliverables:**
- PaymentsMCP server with Exa search tool (1 credit) + a second tool
- Registered agent + plan on Nevermined sandbox
- Self-test: subscriber account orders plan, gets token, calls tool, credits burn
- Listed in hackathon marketplace spreadsheet

**This is a standalone MCP server, not the gateway yet.** The gateway wraps this in Phase 2.

### Phase 2: Two-Tool Gateway (Thursday night / Friday morning)

Build the gateway that fronts all services with `find_service` + `buy_and_call`.

**Deliverables:**
- Gateway MCP server on separate port
- Catalog index with embeddings (in-memory, numpy)
- `find_service` returns top-k matches with prices
- `buy_and_call` proxies to upstream services, returns result + cost
- Transaction logging (every buy_and_call logged)

### Phase 3: Demo Polish (Friday, by 4PM code freeze)

**Deliverables:**
- Dynamic pricing (three-tier surge, 15-min rolling window)
- Marketplace feed (WebSocket, scrolling events)
- More services in catalog (from walking around + autonomous wrapping)
- The zing — whichever direction has gravity by Friday

## Components

| Component | Purpose | Phase |
|-----------|---------|-------|
| **Exa MCP Server** | First paid service, proves the flow | P1 |
| **Nevermined Registration** | Agent + plan + self-test | P1 |
| **Gateway Server** | Two-tool MCP interface for buyers | P2 |
| **Catalog Index** | Embeddings over tool descriptions for `find_service` | P2 |
| **Transaction Log** | Every buy_and_call logged with buyer, service, price, timestamp | P2 |
| **Pricing Engine** | Surge pricing based on demand | P3 |
| **Marketplace Feed** | WebSocket live feed for demo | P3 |
| **Wrapper Agent** | Autonomous discovery + wrapping via simple-loop | P3 |

## Tech Stack

- **Language:** Python 3.10+
- **MCP + Payments:** `payments-py[mcp]` (PaymentsMCP wraps FastMCP + Nevermined billing)
- **HTTP:** FastAPI + uvicorn (for any non-MCP endpoints), httpx (client)
- **Embeddings:** OpenAI `text-embedding-3-small` (for catalog search)
- **Search:** Exa API (first wrapped service)
- **Agent harness:** simple-loop (for autonomous wrapper agent on ScavieFae)

## Success Criteria

1. First paid transaction by 8PM Thursday
2. 3+ other teams' agents buying from us
3. Dynamic pricing responding to demand
4. At least one other team listing their API through us
5. Demo tells a story, not just shows plumbing
