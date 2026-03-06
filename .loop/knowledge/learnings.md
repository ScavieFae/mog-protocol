# Project Learnings

Agent-writable knowledge base. Add findings, patterns, and gotchas here.

## Portfolio Patterns

### Reading demand signals

The gateway `/health` endpoint returns active services, recent transactions, and surge data. Use it to decide where to invest:

```bash
curl -s https://beneficial-essence-production-99c7.up.railway.app/health | python -m json.tool
```

Look for:
- `surge_multiplier > 1.5` on a service → high demand, consider substitutes or price raise
- services with zero recent transactions → potential kill candidates
- `portfolio.balance` — if >20cr and ROI >0, reinvest; if <10cr, pause new investments

### Proposing a hypothesis before wrapping

Before spending credits to wrap an API, record the investment decision:

```python
from src.portfolio import PortfolioManager
p = PortfolioManager()

# Check if investment makes sense first
if p.should_invest(cost=1, expected_revenue=8):
    hyp_id = p.propose(
        service_id="openmeteo_weather",
        thesis="Free weather API, agents need weather. Expect 8cr in 2hrs.",
        expected_revenue=8,
        cost_to_validate=1
    )
    # ... do the wrap work ...
    p.spend(1, "openmeteo_weather", "API validation call")
    p.update_hypothesis(hyp_id, "wrapped")
```

### Using should_invest() as a gate

`should_invest(cost, expected_revenue)` returns True if:
- expected ROI > 2x (expected_revenue / cost >= 2)
- current balance >= cost

Never wrap a service without checking this first if you have a hypothesis ID from the conductor.

### Service implementation rules

- All handlers go in `src/services.py`
- Handlers MUST be synchronous (not async). Use `httpx.get()` not `aiohttp`.
- Handlers return a JSON string (use `json.dumps()`), not a dict
- Register in the `CATALOG` dict at the bottom of `src/services.py`
- Free APIs (no key required) = 100% margin = best investment targets

### Gateway URL

Production: `https://beneficial-essence-production-99c7.up.railway.app`

### PortfolioManager quick reference

```python
from src.portfolio import PortfolioManager
p = PortfolioManager()

p.spend(credits, service_id, description)       # record a cost
p.earn(credits, service_id, description)        # record revenue (usually gateway does this)
p.propose(service_id, thesis, expected_revenue, cost_to_validate)  # returns hyp_id
p.update_hypothesis(hyp_id, status)             # proposed|validating|validated|wrapped|earning|killed
p.should_invest(cost, expected_revenue)         # True if ROI > 2x and budget allows
p.get_summary()                                 # dashboard dict for /health and conductor
p.get_active_hypotheses()                       # list of non-killed hypotheses
p.get_best_performers(top_k=3)                  # ranked by actual_revenue
```

## Agent Toolkit (src/toolkit.py)

Available tools for autonomous API acquisition:
- `browse.navigate(url)` — read any web page, even client-rendered (via Browserbase)
- `browse.fill_form(fields)` / `browse.click(selector)` — complete signup flows
- `email.create_inbox(label)` — get a working email address (via AgentMail)
- `email.check_inbox(inbox_id, wait_seconds=30)` — poll for verification emails
- `email.extract_verification(message)` — extract 6-digit codes or verify links
- `vault.store(name, value)` / `vault.get(name)` — persist API keys across sessions
- `blockers.report(service_id, blocker_type, ...)` — structured failure reporting
- `research.social_comments(domain, query)` — mine demand signals from social media
- `research.fetch_archived(url)` — read paywalled articles via archive.ph

When blocked by signup:
1. Check vault first — maybe a previous session already got the key
2. Try browse + email flow
3. If still blocked (CAPTCHA, etc.), file blocker report with recommendation=ESCALATE

Blocker types: signup_required, api_key_needed, paywall, rate_limited, auth_flow, captcha, other
Recommendations: ESCALATE (human needed), RETRY_WITH_TOOL (try toolkit), SKIP (not worth it), DEFER (try later)

Sellable toolkit services in catalog: browser_navigate (5cr), agent_email_inbox (2cr), social_search (2cr), archive_fetch (1cr), circle_faucet (1cr). These are revenue-generating wrappers of the above toolkit methods.

### Killing underperformers

If a hypothesis has been `status="wrapped"` for >1hr and `actual_revenue == 0`, it should be killed. The conductor checks this on each heartbeat. Workers can kill manually:

```python
p.update_hypothesis("hyp-002", "killed")
# Note in diary: [scaviefae] Killed hyp-002 (service_id) — zero revenue after 1hr
```
