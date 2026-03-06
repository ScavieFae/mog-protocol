# Buy from Mog Markets

You are helping a hackathon team connect their agent to Mog Markets, an API marketplace. Generate a complete, copy-paste-ready connection guide.

The buyer needs a Nevermined API key from nevermined.app with all 4 permissions enabled. They already have 20 USDC from signup.

---

Output the following exactly, as a single markdown block the user can copy whole:

---

## Mog Markets -- API Marketplace for Agents

11+ services. Web search, summarization, image generation, weather, geolocation, hackathon guides. Two tools, one MCP connection. 1 USDC = 1 credit.

### Step 1: Subscribe (run once in Python)

```bash
pip install payments-py
```

```python
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_NVM_KEY", environment="sandbox")
)

PLAN_ID = "60859172884142288164507163059546691936422006932528002950292307302678850457887"
payments.plans.order_plan(PLAN_ID)
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
print(token)
```

Save that token. Bigger packs: 5 USDC/10 credits (plan `87533285832696660011690943385915459855771974607401696593091951593047968932457`), 10 USDC/20 credits (plan `107388892078779776783316313571466544272023725956678321074411803867639782898854`).

### Step 2: Add MCP config

Add to your `.mcp.json` or Claude Desktop config:

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

### Step 3: Use it

Your agent now has two tools:

- **find_service** -- search available services (free, no credits)
- **buy_and_call** -- call a service (costs credits)

### Services

| Service | Credits | What it does |
|---------|---------|-------------|
| `exa_search` | 1 | Web search -- snippets + URLs |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization |
| `nano_banana_pro` | 10 | Image generation from text |
| `open_meteo_weather` | 1 | Weather forecast |
| `ip_geolocation` | 1 | IP-to-location lookup |
| `hackathon_discover` | 1 | Find agents on the hackathon portal |
| `hackathon_onboarding` | 1 | Nevermined setup guide |
| `hackathon_pitfalls` | 1 | PaymentsMCP gotchas |
| `hackathon_all` | 1 | All hackathon docs in one call |

### Suggested prompt for your agent

> You have access to the mog-marketplace MCP server. Use `find_service` to browse available APIs, then `buy_and_call` with a `service_id` and `params` to use them. Start by searching for what you need.

### curl test

```bash
curl -X POST https://beneficial-essence-production-99c7.up.railway.app/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"find_service","arguments":{"query":"web search"}}}'
```

---

Do NOT add any commentary, preamble, or explanation outside the guide. The output should be the guide itself, ready to copy.
