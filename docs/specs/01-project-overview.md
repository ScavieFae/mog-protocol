# Mog Protocol — Project Overview

**Classification: NECESSARY**

## What This Is

An autonomous agent marketplace that discovers APIs, evaluates ROI of wrapping them as MCP servers, generates the servers, prices them dynamically, and sells access to other agents — all via Nevermined payment rails.

## Core Thesis

API providers ship 600 endpoints. Agents need 12. We sit at the transaction layer, see demand in real time, and become a better packager of their API than they are. The marketplace scales; the buyer agent's context stays two tools wide.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Mog Protocol                    │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Discovery │  │ Evaluator│  │   Generator   │  │
│  │  (Exa /   │→ │  (ROI    │→ │  (OpenAPI →   │  │
│  │  Apify)   │  │  logic)  │  │  MCP server)  │  │
│  └──────────┘  └──────────┘  └───────┬───────┘  │
│                                      │          │
│  ┌───────────────────────────────────┴────────┐  │
│  │              Gateway Server                │  │
│  │  find_service(query, budget) → matches     │  │
│  │  buy_and_call(service_id, params) → result │  │
│  │  [Nevermined @requires_payment inside]     │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Pricing  │  │ Catalog  │  │   Metrics /   │  │
│  │  Engine   │  │  Index   │  │   Analytics   │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
└─────────────────────────────────────────────────┘
```

## Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| **Gateway Server** | Two-tool MCP interface for buyers | P0 — this IS the product |
| **Wrapper/Generator** | OpenAPI spec → MCP server with billing | P0 — no inventory without it |
| **Nevermined Integration** | `@requires_payment` on all tools | P0 — mandatory for hackathon |
| **Catalog Index** | Embeddings over tool descriptions for `find_service` | P0 — gateway needs search |
| **Pricing Engine** | Dynamic/surge pricing based on demand | P1 — differentiator |
| **Discovery Agent** | Find APIs, evaluate ROI, decide whether to wrap | P1 — autonomous loop |
| **Metrics/Analytics** | Track revenue, usage, demand signals | P1 — feeds pricing + demo |
| **Zing Layer** | Missed connections feed, spot market, etc. | P2 — demo polish |

## Timeline

**Thursday by 8PM:** Manual wrap of 1-2 APIs → listed via Nevermined → first transaction. Gateway with `find_service` + `buy_and_call` working.

**Friday by 4PM (code freeze):** Autonomous discovery loop running. Dynamic pricing active. Enough transactions to show economic behavior. Demo-ready.

## Tech Stack

- **Language:** Python 3.10+
- **Server:** FastAPI
- **MCP generation:** FastMCP (`from_openapi()`)
- **Payments:** Nevermined `payments-py`, `@requires_payment`
- **Search/Discovery:** Exa API
- **Scraping:** Apify
- **Embeddings:** OpenAI `text-embedding-3-small` (for catalog search)
- **Agent framework:** Strands SDK or direct Claude
- **Harness:** simple-loop (for autonomous wrapper agent)

## Success Criteria

1. First paid transaction by 8PM Thursday
2. 3+ other teams' agents buying from us
3. Dynamic pricing responding to demand
4. At least one other team listing their API through us
5. Demo tells a story, not just shows plumbing
