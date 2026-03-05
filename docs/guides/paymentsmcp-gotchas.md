# PaymentsMCP Gotchas — What We Learned So You Don't Have To

We spent Thursday morning fighting these so you can spend it building. Every item here cost us 15-60 minutes.

---

## 1. `payments-py[mcp]` doesn't exist

The hackathon docs say to install `payments-py[mcp]`. This extra doesn't exist in payments-py 1.3.x. `PaymentsMCP` is in the core package.

**What to do:**
```bash
pip install payments-py fastapi
```

`fastapi` must be installed separately — `PaymentsMCP` imports it at runtime.

## 2. `PaymentsMCP.start()` returns immediately

You'd expect `await mcp.start(port=3000)` to block until the server shuts down. It doesn't. The server starts in the background and `start()` returns a dict.

**Your server will exit immediately** if you don't handle this:

```python
# WRONG — server starts then process exits
async def main():
    await mcp.start(port=3000)

# RIGHT — block until interrupted
async def main():
    result = await mcp.start(port=3000)
    stop = result.get("stop") if isinstance(result, dict) else None
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        if stop:
            await stop()
```

## 3. One API key does everything

The docs describe "builder keys" and "subscriber keys" as if they're different accounts. They're not — at least in sandbox.

One key with all four permissions (Register, Purchase, Issue, Redeem) works for:
- Registering agents and plans (builder role)
- Subscribing to plans (subscriber role)
- Getting x402 tokens (subscriber role)
- Settling credits (builder role)

**Don't waste time creating a second account** unless you specifically need distinct wallet addresses (e.g., for showing cross-agent transactions to judges).

## 4. `agent_definition_url` is metadata, not a real URL

When you register an agent:
```python
agent_api=AgentAPIAttributes(
    agent_definition_url="mcp://mog-exa/tools/*",
)
```

That `mcp://` URL is **not resolvable**. Nevermined doesn't proxy MCP calls. It's just metadata stored in the registry. Buyer agents need your actual server URL (like `https://your-app.up.railway.app/mcp`) shared out-of-band — spreadsheet, docs, direct message.

## 5. Nevermined has no search

`GET /agents` returns a flat list. No filtering, no keyword search, no semantic matching. The hackathon uses a Google Sheet as the actual discovery mechanism.

If your agent needs to discover services programmatically, you need to build that yourself (or use ours — that's literally what our gateway does).

## 6. `get_free_price_config()` means free to subscribe, not free to use

This confused us. "Free price" means the plan subscription costs $0. Buyers still burn credits per request. The credits are granted on subscribe (via `credits_granted` in the dynamic credits config), then consumed by `@mcp.tool(credits=N)`.

```python
price_config=get_free_price_config(),        # $0 to subscribe
credits_config=get_dynamic_credits_config(
    credits_granted=100,                      # buyer gets 100 credits
    min_credits_per_request=1,
    max_credits_per_request=10,
),
```

## 7. The x402 token is reusable

You don't need a new token per request. Get one token, use it for all calls until it expires. This matters for performance — token generation hits Nevermined's API.

```python
# Get once
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]

# Use many times
for query in queries:
    resp = httpx.post(url, headers={"Authorization": f"Bearer {token}"}, ...)
```

## 8. Railway deployment: respect the PORT env var

If you deploy to Railway, it injects a `PORT` environment variable. Your server must bind to it:

```python
port = int(os.getenv("PORT", os.getenv("MY_DEFAULT_PORT", "3000")))
```

Railway will kill your deployment if you bind to a hardcoded port.

## 9. Dynamic credits need a callable, not a number

For variable pricing per tool call:

```python
# WRONG — this is a static number
@mcp.tool(credits=5)

# RIGHT — function receives context, returns credits
def dynamic_price(ctx: dict) -> int:
    service_id = ctx.get("args", {}).get("service_id", "")
    return lookup_price(service_id)

@mcp.tool(credits=dynamic_price)
```

The `ctx` dict has `args` (the tool call arguments), which you can use to determine the price.

## 10. Health check endpoint

PaymentsMCP automatically creates a `/health` endpoint. Use it for deployment health checks (Railway, Docker, etc.). It returns:

```json
{"status": "ok", "service": "your-service-name", "timestamp": "..."}
```

---

*From the Mog Protocol team. We built an API marketplace on PaymentsMCP and hit every one of these walls. You're welcome.*
