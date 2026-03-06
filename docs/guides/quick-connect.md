# Connect to Mog Markets

You need a Nevermined API key from [nevermined.app](https://nevermined.app) with all 4 permissions enabled.

## Subscribe

```bash
pip install payments-py httpx
```

```python
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_KEY", environment="sandbox")
)

PLAN_ID = "9661082042009636068072391467054896427087238025772062250717418964278633341785"
payments.plans.order_plan(PLAN_ID)
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
```

## Option A: MCP Config

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

Your agent gets two tools: `find_service` (free) and `buy_and_call` (costs credits).

## Option B: Direct HTTP

```python
import httpx

GATEWAY = "https://beneficial-essence-production-99c7.up.railway.app/mcp"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

# Find services
resp = httpx.post(GATEWAY, headers=headers, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "image generation"}}
}, timeout=30)
print(resp.json()["result"]["content"][0]["text"])

# Buy a service
resp = httpx.post(GATEWAY, headers=headers, json={
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "nano_banana_pro",
        "params": {"prompt": "a sunset over san francisco"}
    }}
}, timeout=30)
print(resp.json()["result"]["content"][0]["text"])
```

## Option C: Onboard Script

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
| `exa_search` | 1 | Semantic web search — snippets + URLs |
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

Use `find_service` to search by what you need — it does keyword matching.

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
- `prompt` (required) — what to generate
- `aspect_ratio` — `1:1`, `16:9`, `4:3`, `3:2` (default `1:1`)
- `resolution` — `1K`, `2K`, `4K` (default `1K`)

The `image_url` is a public URL you can open directly. 10 credits per image.

---

## curl

```bash
curl -X POST https://beneficial-essence-production-99c7.up.railway.app/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"buy_and_call","arguments":{
         "service_id":"nano_banana_pro",
         "params":{"prompt":"a sunset over san francisco","resolution":"1K"}
       }}}'
```
