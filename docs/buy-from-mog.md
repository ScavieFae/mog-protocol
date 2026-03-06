# Buy from Mog Markets

API marketplace for agents. 11+ services (web search, summarization, image gen, weather, more). Two tools, one MCP connection.

## 1. Subscribe (one-time)

You need a Nevermined API key from [nevermined.app](https://nevermined.app). Your wallet already has 20 USDC from signup.

```python
pip install payments-py
```

```python
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_NVM_KEY", environment="sandbox")
)

# Free trial = 3 credits
PLAN_ID = "52344374255582061362376941484417434816120915438329652344828008233054799099083"
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
      "url": "https://beneficial-essence-production-99c7.up.railway.app/mcp",
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

## 3. Services

| Service | Credits | What it does |
|---------|---------|-------------|
| `exa_search` | 1 | Web search with snippets + URLs |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization |
| `nano_banana_pro` | 10 | Image generation from text |
| `open_meteo_weather` | 1 | Weather forecast |
| `ip_geolocation` | 1 | IP-to-location lookup |
| `hackathon_discover` | 1 | Find agents on the portal |
| `hackathon_onboarding` | 1 | Nevermined setup guide |
| `hackathon_pitfalls` | 1 | PaymentsMCP gotchas |
| `hackathon_all` | 1 | All hackathon docs in one call |

## Plans

| Plan | Price | Credits |
|------|-------|---------|
| Free Trial | Free | 3 |
| Starter | 1 USDC | 1 |
| Standard | 5 USDC | 10 |
| Pro | 10 USDC | 25 |

See [quick-connect.md](docs/guides/quick-connect.md) for plan IDs.
