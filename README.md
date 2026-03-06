# Mog Markets

**API marketplace for AI agents.** 22 services behind one endpoint. Two tools, ~200 tokens, pay per call.

Your agent gets `find_service` (free) and `buy_and_call` (costs credits). Search first, see prices, then buy. No API keys to manage, no subscriptions, no context bloat.

**Gateway:** `https://api.mog.markets/mcp`

---

## For Agents: Connect in 60 Seconds

Add this to your MCP config. Done.

```json
{
  "mcpServers": {
    "mog-markets": {
      "type": "http",
      "url": "https://api.mog.markets/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_X402_TOKEN"
      }
    }
  }
}
```

Your agent now has two tools. `find_service` to search the catalog (free), `buy_and_call` to execute any service (costs credits). That's the entire interface — 22 services, same two tools.

---

## Quick Start (Python)

```python
from payments_py import Payments, PaymentOptions

# 1. Connect to Nevermined (get API key at nevermined.app)
payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_NVM_KEY", environment="sandbox")
)

# 2. Subscribe to the free plan (100 credits)
FREE_PLAN = "100055324343248574008048211366287624670698094501751189055453802807316586516007"
payments.plans.order_plan(FREE_PLAN)

# 3. Get access token
token = payments.x402.get_x402_access_token(FREE_PLAN)["accessToken"]

# 4. Call the gateway
import httpx
resp = httpx.post("https://api.mog.markets/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "web search"}}
})
print(resp.json()["result"]["content"][0]["text"])
```

Install: `pip install payments-py httpx`

---

## Services

22 services live behind the gateway. Use `find_service` to discover them, or reference this table directly.

| Service | Credits | Description |
|---------|---------|-------------|
| `exa_search` | 1 | Semantic web search |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization |
| `nano_banana_pro` | 10 | Image generation |
| `open_meteo_weather` | 1 | Weather forecast |
| `ip_geolocation` | 1 | IP location lookup |
| `frankfurter_fx_rates` | 1 | Live/historical FX rates |
| `hacker_news_top` | 2 | Top Hacker News stories |
| `newton_math` | 2 | Symbolic math operations |
| `qr_code` | 1 | QR code generation |
| `hackathon_discover` | 1 | Find hackathon agents |
| `hackathon_portal` | 1 | Hackathon marketplace content |
| `hackathon_onboarding` | 1 | Nevermined onboarding guide |
| `hackathon_pitfalls` | 1 | PaymentsMCP gotchas |
| `hackathon_all` | 1 | All hackathon context in one call |
| `debug_seller` | 1 | Diagnose other teams' seller agents |
| `browser_navigate` | 5 | Headless browser navigation |
| `agent_email_inbox` | 1 | Check agent email inbox |
| `social_search` | 1 | Twitter/social search |
| `archive_fetch` | 1 | Wayback Machine content |
| `circle_faucet` | 1 | USDC testnet faucet |
| `zeroclick_search` | 1 | ZeroClick ad-powered search |

Prices shown are base rates. Surge pricing may apply during high demand (see How It Works).

---

## Plans

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Free (Sponsored) | Free | 100 | `100055324343248574008048211366287624670698094501751189055453802807316586516007` |
| Starter | 1 USDC | 1 | `27532529988899010156793041100542920191141640561034683667962973311488756564499` |
| Standard | 5 USDC | 10 | `6476982684193144215967979389100088950230657664983966011439423784485034538208` |
| Pro | 10 USDC | 25 | `29001175520261924428527314088863841592234134735048963980654691130902766240562` |
| 24h Unlimited | 100 USDC | Unlimited | `44434032783531077541058729887091039457805308156564831638506837872259119558776` |

Start with the free plan. 100 credits covers serious exploration of the catalog. Paid plans settle on-chain via USDC on Base Sepolia. Card payments supported via Stripe delegation.

---

## How It Works

### Two-Tool Gateway (Lazy MCP)

Standard MCP dumps every tool into agent context on connect. 30 tools = ~6,000 tokens of permanent context. Tool selection accuracy degrades — research shows retrieval-first improves tool selection from 13% to 43%.

Mog Markets inverts this. Your agent always sees exactly two tools regardless of how many services exist behind the gateway. Search narrows the space, then you buy what you need. 22 services today, 200 tomorrow — still ~200 tokens of context.

### Dynamic Surge Pricing

Prices adjust in real time using a 4-signal model:

- **Volume tier** — call count in a 15-minute window triggers 1x/1.5x/2x base tiers
- **Velocity** — accelerating call rate (5m vs 15m) boosts the multiplier
- **Demand pressure** — searches exceeding purchases signal latent demand
- **Cooldown decay** — after a surge, price steps down 0.1x every 2 minutes

Multiplier range: 1x to 3x base price. The `_meta` field in every response shows exactly what you paid and why.

### TrustNet Reviews

Every successful `buy_and_call` response includes a review prompt. Buyers can rate services (1-10) via a free REST API — no auth required. Scores feed back into discovery ranking.

### Observability

All transactions log to Helicone for leaderboard tracking. The `/health` endpoint exposes live per-service stats: call counts, success rates, latency, revenue, and surge state.

---

## For Judges

**The problem**: MCP's all-tools-at-once design breaks down at marketplace scale. Agents can't comparison shop, can't see prices before committing, and context windows fill with tool descriptions they'll never use.

**What we built in 36 hours**:

- A two-tool gateway pattern that keeps agent context constant regardless of catalog size
- 22 wrapped services from 12 different API providers, each monetized per-call via Nevermined
- Dynamic surge pricing with a 4-signal model operating on 15-minute rolling windows
- TrustNet integration for decentralized service reviews
- A portfolio manager tracking P&L and investment hypotheses per service
- An autonomous agent colony (scout, worker, supervisor) that finds APIs, wraps them, and quality-checks the results
- Helicone observability layer for full transaction tracing
- Both crypto (USDC on Base Sepolia) and fiat (Stripe delegation) payment paths
- Free sponsored tier with contextual ad injection — a second revenue model beyond credits

**What makes it different**: This isn't a static API wrapper. The marketplace has economic behavior — surge pricing responds to demand, agents can comparison shop across services, and the catalog grows autonomously. The two-tool pattern is a genuine architectural contribution to how agents should interact with large tool sets.

---

## Project Structure

```
src/gateway.py       — Two-tool MCP gateway (find_service + buy_and_call)
src/services.py      — All 22 service handlers + catalog registration
src/catalog.py       — ServiceCatalog (embedding search + keyword fallback)
src/pricing.py       — Dynamic surge pricing engine
src/portfolio.py     — P&L tracking per service
src/supervisor.py    — Autonomous quality control
src/telemetry.py     — Event logging and stats
src/helicone.py      — Helicone observability integration
src/ads.py           — Contextual ad injection for free tier
docs/specs/          — Design specs (numbered, read in order)
docs/research/       — API scout reports and competitive analysis
docs/guides/         — Quick-connect, first transaction, gotchas
```

---

## Links

- [Quick Connect Guide](docs/guides/quick-connect.md) — subscribe, connect, start buying
- [First Transaction Guide](docs/guides/first-transaction.md) — full walkthrough with code
- [PaymentsMCP Gotchas](docs/guides/paymentsmcp-gotchas.md) — save yourself hours of debugging
- [Gateway Health](https://api.mog.markets/health) — live service stats and transaction feed
- [GitHub Issues](https://github.com/ScavieFae/mog-protocol/issues)

---

*Built at the Nevermined Autonomous Business Hackathon, March 5-6, 2026, AWS Loft SF.*
