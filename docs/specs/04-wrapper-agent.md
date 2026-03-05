# Wrapper Agent — Autonomous API Wrapping Pipeline

**Classification: NECESSARY (for "autonomous business" judging criteria)**

## What It Does

Discovers APIs, evaluates whether wrapping them is ROI-positive, generates the MCP server, lists it in the marketplace. Runs autonomously via simple-loop while Mattie does in-person sales.

## Pipeline Stages

### Stage 1: Discovery

Input sources:
- Manual: "wrap Exa search" (Thursday morning, fast path to first transaction)
- Walk-around: "Team 7 uses Weatherstack API, here's their key"
- Autonomous: Exa search for OpenAPI specs, API directories
- Demand-driven: `find_service` queries with 0 results → gaps to fill

### Stage 2: Evaluation (the novel part)

```python
def should_wrap(api_info: dict) -> dict:
    """
    Returns { wrap: bool, reasoning: str, suggested_price: int }

    Factors:
    - upstream_cost: What does each API call cost us?
    - spec_quality: Does a clean OpenAPI spec exist, or do we need to scrape?
    - estimated_demand: How many agents at this hackathon need this?
    - competition: Did someone else already list this?
    - generation_effort: How complex is the API? (endpoint count, auth model)
    - margin: Can we price above cost and below alternatives?
    """
```

At hackathon scale, this is an LLM call with structured output, not a model. Feed it the factors, get a decision. The judgment is the point — it's what makes this an autonomous business, not an autonomous wrapper.

### Stage 3: Generation

```python
# Happy path: clean OpenAPI spec
from fastmcp import FastMCP
server = FastMCP.from_openapi(spec_url, name="weatherstack-mcp")

# Sad path: no spec, just docs
# Use Apify to scrape docs → LLM to generate tool definitions → manual FastMCP
```

**Quality step:** Don't wrap all 600 endpoints. The LLM selects the 5-15 most useful based on likely agent needs. Write good descriptions that tell agents *when* and *why* to use each tool, not just *what* it does.

### Stage 4: Billing Integration

```python
from payments_py import Payments
from payments_py.utils import require_payment

@mog.tool()
@requires_payment(payments=payments, plan_id=PLAN_ID, credits=price, agent_id=AGENT_ID)
def weatherstack_current(location: str) -> dict:
    return requests.get(f"https://api.weatherstack.com/current?query={location}").json()
```

### Stage 5: Listing

Register in our catalog index (embeddings + metadata). Announce via marketplace spreadsheet. Optionally push to ZeroClick for agent-facing ads.

## Simple-Loop Integration

```
Brief: "Discover and wrap APIs for the Mog Protocol marketplace"
Goal: List 5+ services by Friday noon
Tasks:
  1. Wrap Exa search (we have keys)
  2. Wrap Anthropic Claude (we have keys)
  3. Check marketplace spreadsheet for gaps
  4. Evaluate and wrap 3 more based on demand signals
Verification: Each listed service responds to a test buy_and_call
Max iterations: 15
```

The conductor evaluates each iteration: did the wrapper successfully list a service? Is it responding to test calls? Are there demand signals to chase?

## Open Questions

- **API key management:** When other teams give us their keys to wrap, where do we store them? .env per service? Vault? At hackathon scale, .env is fine.
- **Deployment:** Do wrapped MCP servers run as separate processes, or all inside the gateway? Single process is simpler. Separate processes scale better. Start single, split if needed.
- **ToS reality:** We're wrapping and reselling API access. At hackathon scale, nobody cares. Worth acknowledging in the demo with a wink.
