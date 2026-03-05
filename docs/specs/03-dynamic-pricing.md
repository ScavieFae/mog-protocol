# Dynamic Pricing / Demand Intelligence Spec

**Classification: NECESSARY (differentiator)**

## Why This Matters

We sit at the transaction layer. We see demand before upstream API providers do. This creates three capabilities:

1. **Surge pricing** — price goes up when demand spikes
2. **Demand-driven curation** — usage data tells us which endpoints to wrap well
3. **Demand intelligence as a product** — sellable insight about what agents actually want

## Pricing Model

### Base Price

Each listed service has a base price set at listing time:

```python
base_price = upstream_cost_per_call * margin_multiplier
# margin_multiplier starts at 2.0x (100% markup)
# adjusted by evaluator based on competition and estimated demand
```

### Surge Multiplier

```python
def get_current_price(service_id: str) -> int:
    base = catalog[service_id].base_price
    recent_calls = count_calls(service_id, window=timedelta(minutes=15))

    if recent_calls > SURGE_THRESHOLD_HIGH:    # e.g., 20 calls in 15 min
        return int(base * 2.0)
    elif recent_calls > SURGE_THRESHOLD_MEDIUM:  # e.g., 10 calls in 15 min
        return int(base * 1.5)
    else:
        return base
```

Keep it simple. Three tiers, 15-minute rolling window. No ML, no dynamic optimization. The point is demonstrating the behavior, not perfecting the algorithm.

### Undercutting

If we detect another team selling a similar service (via marketplace spreadsheet or our own find_service hitting competitors), we can price below them:

```python
competitor_price = check_competitors(service_category)
if competitor_price and our_base_price > competitor_price:
    our_price = max(competitor_price - 1, upstream_cost + 1)  # undercut but stay profitable
```

This is P2 / zing territory but architecturally trivial if we have competitor awareness.

## Data We Collect

Every `buy_and_call` logs:

```python
{
    "timestamp": "...",
    "service_id": "exa-search-v1",
    "buyer_agent_id": "team-7-agent",
    "query_used_in_find": "semantic web search",  # what they searched for
    "price_charged": 3,
    "surge_multiplier": 1.5,
    "latency_ms": 420,
    "success": true
}
```

### Derived Signals

- **Hot tools:** Which services are getting repeat calls?
- **Unmet demand:** `find_service` queries that returned 0 results → gaps in our catalog
- **Price sensitivity:** Do buyers stop buying when surge kicks in, or keep going?
- **Switching behavior:** Does a buyer try service A, then switch to B next time?

These signals feed back into the autonomous wrapper agent: "Lots of agents searching for 'PDF extraction' but we don't have it. Evaluate and wrap."

## Demo Value

A live price ticker showing surge pricing in action is visceral. Judges can watch prices move as agents trade. This is the closest thing to a stock market for API access — and it makes the marketplace feel alive.

## Implementation Priority

1. **Transaction logging** — P0, needed for everything else
2. **Three-tier surge pricing** — P1, simple and demo-friendly
3. **Unmet demand tracking** — P1, feeds the autonomous loop
4. **Competitor undercutting** — P2, zing
5. **Price ticker visualization** — P2, demo polish
