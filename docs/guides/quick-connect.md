# Connect to Mog Markets

You need a Nevermined API key from [nevermined.app](https://nevermined.app) with all 4 permissions enabled. Your wallet needs USDC on Base Sepolia (you got 20 on registration).

## Pricing

| Pack | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Starter | 1 USDC | 1 call | `60859172884142288164507163059546691936422006932528002950292307302678850457887` |
| Standard | 5 USDC | 10 calls | `87533285832696660011690943385915459855771974607401696593091951593047968932457` |
| Pro | 10 USDC | 20 calls | `107388892078779776783316313571466544272023725956678321074411803867639782898854` |

1 credit = 1 API call. Pick the plan that fits.

## Subscribe + Buy

```bash
pip install payments-py httpx
```

```python
from payments_py import Payments, PaymentOptions
import httpx, json

# 1. Connect to Nevermined
payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_NVM_KEY", environment="sandbox")
)

# 2. Subscribe (1 USDC = 1 API call)
PLAN_ID = "60859172884142288164507163059546691936422006932528002950292307302678850457887"
payments.plans.order_plan(PLAN_ID)

# 3. Get access token
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]

# 4. Search for services (free)
GATEWAY = "https://beneficial-essence-production-99c7.up.railway.app/mcp"
resp = httpx.post(GATEWAY, headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "web search"}}
}, timeout=30)
print(resp.json()["result"]["content"][0]["text"])

# 5. Buy a service (costs 1 credit)
resp = httpx.post(GATEWAY, headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "exa_search",
        "params": {"query": "latest AI research", "max_results": 3}
    }}
}, timeout=30)
print(resp.json()["result"]["content"][0]["text"])
```

## MCP Config

Add to your `.mcp.json` so your agent sees `find_service` and `buy_and_call`:

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

## Onboard Script

```bash
git clone https://github.com/ScavieFae/mog-protocol.git
cd mog-protocol
pip install payments-py httpx
python onboard.py YOUR_NVM_API_KEY
```

Prints your token, MCP config, service list, and a curl example.

---

## Services

| Service | Credits | What It Does |
|---------|---------|-------------|
| `exa_search` | 1 | Semantic web search -- snippets + URLs |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization (bullets, paragraph, structured) |
| `nano_banana_pro` | 10 | Image generation from text prompts |
| `open_meteo_weather` | 1 | Weather forecast for any location |
| `ip_geolocation` | 1 | Geographic location for any IP address |
| `hackathon_discover` | 1 | Find agents on the hackathon portal |
| `hackathon_portal` | 1 | Ingested hackathon marketplace content |
| `hackathon_onboarding` | 1 | Nevermined onboarding guide |
| `hackathon_pitfalls` | 1 | 9 PaymentsMCP gotchas |
| `hackathon_all` | 1 | Portal + onboarding + pitfalls in one call |

Use `find_service` to search by what you need -- it does keyword matching.

---

## Image Generation Example

```python
resp = httpx.post(GATEWAY, headers=headers, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "nano_banana_pro",
        "params": {
            "prompt": "A cyberpunk cat riding a skateboard",
            "aspect_ratio": "1:1",
            "resolution": "1K"
        }
    }}
}, timeout=60)
```

Returns:
```json
{
    "image_url": "https://fal.media/files/...",
    "width": 1024,
    "height": 1024,
    "content_type": "image/png"
}
```

Parameters:
- `prompt` (required) -- what to generate
- `aspect_ratio` -- `1:1`, `16:9`, `4:3`, `3:2` (default `1:1`)
- `resolution` -- `1K`, `2K`, `4K` (default `1K`)

The `image_url` is a public URL you can open directly. 10 credits per image.

---

## curl

```bash
curl -X POST https://beneficial-essence-production-99c7.up.railway.app/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"buy_and_call","arguments":{
         "service_id":"exa_search",
         "params":{"query":"autonomous AI agents","max_results":3}
       }}}'
```
