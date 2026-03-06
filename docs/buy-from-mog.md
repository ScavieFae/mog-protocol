# Buy from Mog Markets

API marketplace for agents. 22 services (web search, summarization, image gen, browser, debugger, math, weather, more). Two tools, one MCP connection.

## 1. Subscribe (one-time)

You need a Nevermined API key from [nevermined.app](https://nevermined.app). Your wallet already has 20 USDC from signup.

```bash
pip install payments-py
```

```python
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_NVM_KEY", environment="sandbox")
)

# Free (Sponsored) plan = 100 credits, no payment needed
PLAN_ID = "100055324343248574008048211366287624670698094501751189055453802807316586516007"
payments.plans.order_plan(PLAN_ID)
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
print(token)  # save this
```

## 2. Connect your agent

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "mog-marketplace": {
      "type": "http",
      "url": "https://api.mog.markets/mcp",
      "headers": {
        "Authorization": "Bearer PASTE_TOKEN_HERE"
      }
    }
  }
}
```

Your agent now has two tools:
- **find_service** -- search what's available (free)
- **buy_and_call** -- use a service (1-10 credits)

## 3. Services (22 total)

| Service | Credits | What it does |
|---------|---------|-------------|
| `exa_search` | 1 | Semantic web search -- snippets + URLs |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization (bullets, paragraph, structured) |
| `nano_banana_pro` | 10 | Image generation from text (Gemini 3 Pro) |
| `open_meteo_weather` | 1 | Weather forecast for any location |
| `ip_geolocation` | 1 | IP-to-location lookup |
| `frankfurter_fx_rates` | 1 | Live/historical FX rates for 29 currencies |
| `hacker_news_top` | 2 | Top Hacker News stories with scores + URLs |
| `newton_math` | 2 | Symbolic math: simplify, factor, derive, integrate |
| `qr_code` | 1 | Generate QR code for any text or link |
| `debug_seller` | 2 | Debug any Nevermined marketplace agent |
| `browser_navigate` | 5 | Headless browser -- read JS-rendered pages |
| `agent_email_inbox` | 2 | Disposable email inbox for signups |
| `social_search` | 2 | Search social media for demand signals |
| `archive_fetch` | 1 | Fetch archived version of any URL |
| `circle_faucet` | 1 | Claim testnet USDC from Circle faucet |
| `zeroclick_search` | 1 | Sponsored search -- deals from 10k+ advertisers |
| `hackathon_discover` | 1 | Find agents on the portal |
| `hackathon_portal` | 1 | Ingested hackathon marketplace content |
| `hackathon_onboarding` | 1 | Nevermined setup guide |
| `hackathon_pitfalls` | 1 | PaymentsMCP gotchas |
| `hackathon_all` | 1 | All hackathon docs in one call |

## Plans

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| **Free (Sponsored)** | Free | 100 | `100055324343248574008048211366287624670698094501751189055453802807316586516007` |
| 24h Unlimited | $100 USDC | Unlimited | `44434032783531077541058729887091039457805308156564831638506837872259119558776` |

See [quick-connect guide](guides/quick-connect.md) for full code examples and MCP config.
