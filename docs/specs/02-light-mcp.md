# Light MCP — Two-Tool Gateway Spec

**Classification: NECESSARY**

## Problem

MCP dumps full tool catalogs into buyer agent context on connect. At 30+ tools, accuracy drops and context bloat kills performance. Research shows retrieval-first patterns improve tool-selection accuracy from 13% → 43%.

## Design

Our marketplace exposes exactly two tools to buyer agents:

### Tool 1: `find_service`

```python
def find_service(query: str, budget: int = None, category: str = None) -> list[ServiceMatch]:
    """
    Semantic search over all listed services.

    Args:
        query: Natural language description of what the agent needs
        budget: Max credits per call (optional, filters results)
        category: Category filter (optional)

    Returns:
        Top 3-5 matches with:
        - service_id: unique identifier
        - name: human-readable name
        - description: what it does, when to use it
        - price: credits per call (current, may reflect surge)
        - provider: who listed it
        - example_params: sample input to understand the interface
    """
```

### Tool 2: `buy_and_call`

```python
def buy_and_call(service_id: str, params: dict) -> ServiceResult:
    """
    Pay for and execute a service in one call.

    Handles Nevermined payment internally — buyer doesn't need
    to manage tokens or payment flows.

    Args:
        service_id: From find_service results
        params: Parameters for the underlying tool

    Returns:
        - result: The actual API response
        - credits_charged: What it cost
        - remaining_budget: Buyer's remaining credits
    """
```

## Implementation

### Catalog Index

- Store tool descriptions + metadata in a simple vector store
- Embed on listing with `text-embedding-3-small`
- `find_service` embeds the query, cosine similarity, top-k
- At hackathon scale (< 50 tools), this can be in-memory with numpy — no need for a vector DB

### Payment Flow (inside `buy_and_call`)

```
1. Buyer calls buy_and_call(service_id, params)
2. Gateway looks up service → gets Nevermined plan_id, price
3. Gateway generates x402 access token on buyer's behalf
4. Gateway proxies call to the actual MCP server with payment token
5. MCP server validates via @requires_payment, executes, returns result
6. Gateway returns result + cost to buyer
```

**Key decision:** The gateway holds the buyer's payment context. Buyer agents don't need to understand Nevermined. They call `buy_and_call` and get results.

### MCP Server Setup

The gateway itself is an MCP server (via FastMCP). Buyer agents connect to it like any other MCP server:

```python
from fastmcp import FastMCP

mog = FastMCP("Mog Protocol", description="API marketplace. Search and buy access to tools.")

@mog.tool()
def find_service(query: str, budget: int = None) -> list[dict]:
    # embed query, search catalog, filter by budget
    ...

@mog.tool()
def buy_and_call(service_id: str, params: dict) -> dict:
    # payment + proxy
    ...
```

## Open Questions

- **Auth model:** How does the buyer agent authenticate with us? Nevermined agent ID? API key on connect? Need to match whatever other teams' agents can handle easily.
- **Error handling:** If the underlying service fails after payment, do we refund? At hackathon scale, probably just return the error and eat it.
- **Rate limiting:** Do we rate-limit per buyer? Probably not for hackathon, but the pricing engine handles this via surge pricing instead.
- **mcpc:** Apify recommends `mcpc`, a lightweight MCP implementation. Need to evaluate whether it's a better fit than FastMCP for the gateway. Neutral — flagged by sponsor, worth a look before committing to FastMCP.
