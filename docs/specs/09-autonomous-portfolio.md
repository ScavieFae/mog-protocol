# Spec 09: Autonomous Portfolio Agent

## What

Give our agents a credit budget, a hypothesis ledger, and P&L tracking. The scout-worker loop becomes an *investor*: it spends credits to validate APIs, wraps the winners, earns credits from buyer traffic, and adjusts strategy based on what's actually selling. Surge pricing feeds back into investment decisions — high-surge services are signals to find substitutes or raise prices.

## Why

The hackathon judges want to see autonomous *economic behavior*, not just plumbing. Right now we have:
- A gateway that charges credits (done)
- Surge pricing that reacts to volume (done)
- A scout that finds APIs and a worker that wraps them (done)

What's missing: the agent doesn't *decide* whether to spend. It has no budget, no hypothesis, no feedback loop. The demo story should be: "Our agent started with 50 credits, hypothesized which APIs would sell, invested credits to validate them, wrapped the winners, earned 80 credits back. Here's the P&L."

## Architecture

### Portfolio State (`src/portfolio.py`)

Single JSON file (`data/portfolio.json`) tracking the agent's economic state:

```python
{
    "budget": {
        "starting_credits": 50,
        "spent": 12,
        "earned": 34,
        "balance": 72          # starting - spent + earned
    },
    "hypotheses": [
        {
            "id": "hyp-001",
            "service_id": "frankfurter_fx_rates",
            "thesis": "FX rates: free API, 1cr cost to wrap, expect 10cr revenue in 2hrs",
            "expected_revenue": 10,
            "cost_to_validate": 1,
            "cost_to_wrap": 0,
            "status": "validated",    # proposed | validating | validated | wrapped | earning | killed
            "actual_revenue": 7,
            "created_at": "2026-03-06T02:00:00Z",
            "resolved_at": "2026-03-06T04:00:00Z"
        }
    ],
    "pnl": [
        {
            "timestamp": "2026-03-06T02:30:00Z",
            "type": "cost",           # cost | revenue
            "service_id": "frankfurter_fx_rates",
            "credits": 1,
            "description": "Validation call via gateway"
        },
        {
            "timestamp": "2026-03-06T03:15:00Z",
            "type": "revenue",
            "service_id": "frankfurter_fx_rates",
            "credits": 3,
            "description": "3 buyer calls at 1cr each"
        }
    ]
}
```

### Portfolio Manager Class

```python
class PortfolioManager:
    def __init__(self, path="data/portfolio.json", starting_credits=50):
        ...

    # Budget
    def spend(self, credits, service_id, description) -> bool:  # False if over budget
    def earn(self, credits, service_id, description) -> None
    @property
    def balance(self) -> int
    @property
    def roi(self) -> float  # (earned - spent) / spent

    # Hypotheses
    def propose(self, service_id, thesis, expected_revenue, cost_to_validate) -> str  # returns hyp id
    def update_hypothesis(self, hyp_id, status, **kwargs) -> None
    def get_active_hypotheses(self) -> list
    def get_best_performers(self, top_k=3) -> list  # by actual_revenue

    # Revenue sync — called by gateway on each buy_and_call
    def record_sale(self, service_id, credits_charged) -> None

    # Decision support
    def should_invest(self, cost, expected_revenue) -> bool:
        """Simple: invest if expected ROI > 2x and we have budget."""

    def get_summary(self) -> dict:
        """Dashboard-ready summary: budget, active hypotheses, top earners, ROI."""
```

### Revenue Flow

The gateway already tracks credits_charged per buy_and_call. We need to:
1. On each successful `buy_and_call`, call `portfolio.record_sale(service_id, credits_charged)` — this is *revenue* for services we own.
2. When the scout validates an API (by calling our own gateway or an external one), call `portfolio.spend()` — this is *cost*.
3. The portfolio file persists across restarts (JSON on disk, not in-memory).

### Surge Pricing Integration

Surge pricing already works. The portfolio adds *strategic* reactions:
- **High surge on our service** = it's selling well. Record as signal. Consider raising base price.
- **High surge on competitor** = demand exists, consider wrapping a substitute.
- The scout reads surge data from `/health` to inform hypotheses.

### Updated Scout Loop

The conductor prompt gets portfolio awareness:

```
1. Read portfolio.json — what's our budget, what's earning, what's losing?
2. Read /health — what's in demand? What's surging?
3. If budget allows and demand signals exist:
   a. Propose hypothesis (expected revenue, cost to validate)
   b. If should_invest() → dispatch validation brief to worker
4. If a wrapped service has zero revenue after 1hr → consider kill/reprice
5. Update portfolio with any revenue since last check
```

### Updated Worker Loop

Worker gets portfolio integration:
- Before wrapping: `portfolio.spend(cost, service_id, "wrapping")`
- After successful wrap: `portfolio.update_hypothesis(hyp_id, "wrapped")`
- On validation calls: `portfolio.spend(cost, service_id, "validation")`

### Health Endpoint Extension

`GET /health` already returns services + transactions. Add portfolio summary:

```json
{
    "portfolio": {
        "balance": 72,
        "roi": 1.83,
        "active_hypotheses": 2,
        "top_earner": "exa_search",
        "total_revenue": 34,
        "total_cost": 12
    }
}
```

## What Gets Built (Brief Sequence)

### Brief 007: Portfolio Core (`src/portfolio.py`)
- PortfolioManager class with budget, hypotheses, P&L ledger
- JSON persistence to `data/portfolio.json`
- Tests for spend/earn/propose/should_invest
- Initialize with 50 credits

### Brief 008: Fix FX Handler + Wire New Services
- Fix `_frankfurter_fx_rates` — it's `async` but gateway calls sync. Convert to sync with `httpx` (not async).
- Verify all 12 services work end-to-end
- Commit the FX handler (currently unstaged)

### Brief 009: Gateway Revenue Tracking
- Wire `portfolio.record_sale()` into `buy_and_call` success path
- Add portfolio summary to `/health` response
- Portfolio loads on gateway startup, saves after each sale

### Brief 010: Autonomous Investment Loop
- Update conductor prompt with portfolio awareness
- Update worker prompt with spend/earn tracking
- Scout reads demand signals + surge data, proposes hypotheses
- Worker validates and wraps, records costs
- Conductor evaluates ROI, kills underperformers
- Update `goals.md` so the loop knows what to do

## Constraints

- Portfolio is JSON-on-disk, not a database. Simplicity over durability.
- Starting budget is configurable via env var `MOG_STARTING_CREDITS` (default 50).
- Revenue tracking is best-effort — if gateway restarts, in-flight sales may be missed. Acceptable for hackathon.
- The autonomous loop should be safe to run overnight. Worst case: it burns through 50 credits of self-buys and idles. It cannot spend real money without human intervention (Nevermined credits are sandbox).

## Demo Story (3 minutes)

1. "We built an autonomous API marketplace."
2. "Our agent starts with 50 credits. It discovers APIs, hypothesizes which ones will sell, and invests credits to validate them."
3. Show portfolio.json: hypotheses proposed, validated, wrapped.
4. Show /health: services live, transactions flowing, surge pricing active.
5. "Overnight, the agent earned 80 credits. Here's the P&L." Show top earners, ROI.
6. "The agent killed one service that wasn't selling and reinvested the savings."
7. Show the garden visualization (Trinity dashboard) — flowers blooming for popular services, wilting for killed ones.
